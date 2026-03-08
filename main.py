# -*- coding: utf-8 -*-
import sys
import pickle
import os
import datetime as dt
from datetime import datetime
from PySide6.QtWidgets import (QApplication, QMainWindow, QTabWidget, 
                               QWidget, QVBoxLayout, QLabel, QPushButton, 
                               QLineEdit, QHBoxLayout, QListWidget, QMessageBox, 
                               QListWidgetItem, QRadioButton, QButtonGroup, 
                               QMenu, QComboBox, QProgressBar)
from PySide6.QtCore import Qt, QTimer

# --- 核心任务类 ---
class Task:
    def __init__(self, name, task_type, target_min, base_points, max_daily=1, checkin_time=""):
        self.name = name
        self.task_type = task_type
        self.target_min = target_min
        self.base_points = base_points
        self.max_daily = max_daily
        self.checkin_time = checkin_time
        self.current_daily = 0  
        self.last_date = datetime.now().strftime("%Y-%m-%d")
        self.elapsed_seconds = 0
        self.is_completed = False
        self.process_points_earned = 0  
        self.last_milestone = 0 

class LearningApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("学习积分助手 v5.2 - 2026 利息+签到增强版")
        self.setGeometry(100, 100, 1150, 850)
        
        # 核心数据
        self.data_file = "learning_data.dat"
        self.total_points = 0
        self.total_interest_earned = 0 
        self.streak_count = 0      
        self.last_checkin_date = ""    
        self.last_interest_date = ""   
        self.all_tasks = []      
        self.time_bank = {}      
        self.history_logs = []   
        self.active_task = None  

        self.init_ui()
        self.load_data() 

        # 计时器
        self.main_timer = QTimer()
        self.main_timer.timeout.connect(self.on_timer_tick)
        self.store_timer = QTimer()
        self.store_timer.timeout.connect(self.update_store_timer)
        self.monitor_timer = QTimer()
        self.monitor_timer.timeout.connect(self.auto_check_reset)
        self.monitor_timer.start(30000) 

    def init_ui(self):
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # 顶部信息栏
        header = QHBoxLayout()
        self.points_label = QLabel(f"💰 总积分: {round(self.total_points, 2)}")
        self.points_label.setStyleSheet("font-size: 26px; color: #E67E22; font-weight: bold;")
        self.interest_label = QLabel(f"📈 累计利息: {round(self.total_interest_earned, 2)}")
        self.interest_label.setStyleSheet("font-size: 16px; color: #27AE60;")
        header.addWidget(self.points_label)
        header.addStretch()
        header.addWidget(self.interest_label)
        self.main_layout.addLayout(header)

        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget)
        
        self.create_task_tab()      
        self.create_checkin_tab()   
        self.create_store_tab()     
        self.create_reward_tab()    
        self.create_stat_tab()      

    # --- 1. 任务面板 (修复丢失字段) ---
    def create_task_tab(self):
        tab = QWidget(); layout = QVBoxLayout(tab)
        
        # 输入行1
        h1 = QHBoxLayout()
        self.t_name_in = QLineEdit(); self.t_name_in.setPlaceholderText("任务名称")
        self.t_min_in = QLineEdit(); self.t_min_in.setPlaceholderText("目标分钟")
        self.t_pts_in = QLineEdit(); self.t_pts_in.setPlaceholderText("总积分")
        h1.addWidget(self.t_name_in); h1.addWidget(self.t_min_in); h1.addWidget(self.t_pts_in)
        
        # 输入行2 (找回的签到次数和截止时间)
        h_ext = QHBoxLayout()
        self.t_max_in = QLineEdit(); self.t_max_in.setPlaceholderText("每日限次 (默认1)")
        self.t_time_in = QLineEdit(); self.t_time_in.setPlaceholderText("截止时间 (例 08:00)")
        h_ext.addWidget(QLabel("详细设置:")); h_ext.addWidget(self.t_max_in); h_ext.addWidget(self.t_time_in)
        
        # 输入行3
        h2 = QHBoxLayout()
        self.t_type_group = QButtonGroup(self)
        self.r1 = QRadioButton("一次性"); self.r1.setChecked(True); self.t_type_group.addButton(self.r1, 0)
        self.r2 = QRadioButton("常规任务"); self.t_type_group.addButton(self.r2, 1)
        self.r3 = QRadioButton("定时签到"); self.t_type_group.addButton(self.r3, 2)
        btn_add = QPushButton("➕ 添加任务"); btn_add.clicked.connect(self.add_task)
        h2.addWidget(self.r1); h2.addWidget(self.r2); h2.addWidget(self.r3); h2.addWidget(btn_add)
        
        layout.addLayout(h1); layout.addLayout(h_ext); layout.addLayout(h2)

        lh = QHBoxLayout()
        self.task_lists = {"一次性": QListWidget(), "常规任务": QListWidget(), "定时签到": QListWidget(), "已完成": QListWidget()}
        for n, lw in self.task_lists.items():
            box = QVBoxLayout(); box.addWidget(QLabel(n))
            lw.itemClicked.connect(self.refresh_display_on_click)
            lw.setContextMenuPolicy(Qt.CustomContextMenu)
            lw.customContextMenuRequested.connect(self.show_task_menu)
            box.addWidget(lw); lh.addLayout(box)
            
        layout.addLayout(lh)

        self.progress_bar = QProgressBar(); self.progress_bar.setFixedHeight(15)
        self.label_reward_info = QLabel("已领奖励: 0 / 总分: 0")
        layout.addWidget(self.progress_bar); layout.addWidget(self.label_reward_info)

        ctrl = QHBoxLayout()
        self.label_task_time = QLabel("计时: 00:00")
        self.btn_s = QPushButton("▶️ 开始计时"); self.btn_s.clicked.connect(self.toggle_task_timer)
        self.btn_f = QPushButton("✅ 结算任务"); self.btn_f.clicked.connect(self.finish_task)
        ctrl.addWidget(self.label_task_time); ctrl.addStretch(); ctrl.addWidget(self.btn_s); ctrl.addWidget(self.btn_f)
        layout.addLayout(ctrl); self.tab_widget.addTab(tab, "任务面板")

    # --- 2. 连续签到 (严格阶梯逻辑) ---
    def create_checkin_tab(self):
        tab = QWidget(); layout = QVBoxLayout(tab)
        self.lbl_streak = QLabel(f"🔥 连续打卡: {self.streak_count} 天")
        self.lbl_streak.setStyleSheet("font-size: 30px; font-weight: bold; color: #E74C3C; margin: 50px;")
        self.lbl_streak.setAlignment(Qt.AlignCenter)
        btn_checkin = QPushButton("📅 点击签到打卡")
        btn_checkin.setFixedSize(300, 100); btn_checkin.setStyleSheet("font-size: 20px; background: #3498DB; color: white; border-radius: 15px;")
        btn_checkin.clicked.connect(self.do_daily_checkin)
        layout.addStretch(); layout.addWidget(self.lbl_streak); layout.addWidget(btn_checkin, 0, Qt.AlignCenter); layout.addStretch()
        self.tab_widget.addTab(tab, "打卡签到")

    def do_daily_checkin(self):
        today = datetime.now().date()
        if self.last_checkin_date:
            last_date = datetime.strptime(self.last_checkin_date, "%Y-%m-%d").date()
            diff = (today - last_date).days
            if diff == 0:
                QMessageBox.information(self, "提醒", "今天已签到！"); return
            elif diff == 1:
                self.streak_count += 1
            else:
                self.streak_count = 1 # 断签重置
        else:
            self.streak_count = 1

        reward = self.streak_count * 5 
        self.total_points += reward
        self.last_checkin_date = today.strftime("%Y-%m-%d")
        self.add_log("奖励", f"连续签到第{self.streak_count}天", reward)
        self.update_all_ui(); self.save_data()
        QMessageBox.information(self, "成功", f"签到成功！获得 {reward} 积分")

    # --- 利息核心逻辑 (资本结息) ---
    def calculate_capital_interest(self):
        today = datetime.now().date()
        if not self.last_interest_date:
            self.last_interest_date = today.strftime("%Y-%m-%d")
            return
            
        last_date = datetime.strptime(self.last_interest_date, "%Y-%m-%d").date()
        days = (today - last_date).days
        
        if days > 0:
            # 每日 0.1% 复利
            earned = self.total_points * 0.001 * days
            if earned > 0:
                self.total_points += earned
                self.total_interest_earned += earned
                self.add_log("系统", f"资本结息({days}天)", round(earned, 4))
                self.last_interest_date = today.strftime("%Y-%m-%d")
                self.update_all_ui()
                self.save_data()

    def update_store_timer(self):
        """消费补偿利息 (0.0166/秒)"""
        c = getattr(self, 'act_c', None)
        if c and self.time_bank.get(c, 0) > 0:
            self.time_bank[c] -= 1
            interest = 0.0166 # 移植自利息版
            self.total_points += interest
            self.total_interest_earned += interest
            m, s = divmod(self.time_bank[c], 60)
            self.label_s_status.setText(f"🔥 {c} | 剩: {m:02d}:{s:02d} | 📈 利息累加中")
            self.update_all_ui()
        else: self.stop_consuming()

    # --- 数据存取 ---
    def save_data(self):
        try:
            rewards = [self.reward_list.item(i).data(Qt.UserRole) for i in range(self.reward_list.count())]
            purchased = [self.purchased_list.item(i).data(Qt.UserRole) for i in range(self.purchased_list.count())]
            with open(self.data_file, "wb") as f:
                pickle.dump({
                    "points": self.total_points, 
                    "interest": self.total_interest_earned, 
                    "streak": self.streak_count, 
                    "last_check": self.last_checkin_date, 
                    "last_interest": self.last_interest_date,
                    "tasks": self.all_tasks, 
                    "bank": self.time_bank, 
                    "logs": self.history_logs, 
                    "rewards": rewards, 
                    "purchased": purchased
                }, f)
        except: pass

    def load_data(self):
        if not os.path.exists(self.data_file): return
        try:
            with open(self.data_file, "rb") as f:
                d = pickle.load(f)
                self.total_points = d.get("points", 0)
                self.total_interest_earned = d.get("interest", 0)
                self.streak_count = d.get("streak", 0)
                self.last_checkin_date = d.get("last_check", "")
                self.last_interest_date = d.get("last_interest", "")
                self.all_tasks = d.get("tasks", [])
                self.time_bank = d.get("bank", {})
                self.history_logs = d.get("logs", [])
                
                # 加载奖励列表
                for r in d.get("rewards", []):
                    it = QListWidgetItem(f"🏆 {r['name']} | {r['pts']}分"); it.setData(Qt.UserRole, r); self.reward_list.addItem(it)
                for p in d.get("purchased", []):
                    it = QListWidgetItem(f"🎁 {p['name']} (已兑换)"); it.setData(Qt.UserRole, p); self.purchased_list.addItem(it)
                
                # 启动时结算资本利息
                self.calculate_capital_interest()
                self.refresh_task_lists(); self.update_all_ui()
        except: pass

    # --- 其余基础功能 (保持不变) ---
    def add_task(self):
        n = self.t_name_in.text(); tp = ["一次性", "常规任务", "定时签到"][self.t_type_group.checkedId()]
        m, p = int(self.t_min_in.text() or 0), int(self.t_pts_in.text() or 0)
        max_d = int(self.t_max_in.text() or 1); c_time = self.t_time_in.text() or ""
        if n: 
            self.all_tasks.append(Task(n, tp, m, p, max_daily=max_d, checkin_time=c_time))
            self.refresh_task_lists(); self.save_data(); self.t_name_in.clear()
            self.t_max_in.clear(); self.t_time_in.clear()

    def update_all_ui(self):
        self.points_label.setText(f"💰 总积分: {round(self.total_points, 2)}")
        self.interest_label.setText(f"📈 累计利息: {round(self.total_interest_earned, 2)}")
        self.lbl_streak.setText(f"🔥 连续打卡: {self.streak_count} 天")
        b = [f"{k}:{v//60}分" for k, v in self.time_bank.items() if v > 0]
        self.bank_display.setText("时长余额: " + (" | ".join(b) if b else "空"))
        self.consume_list.clear(); [self.consume_list.addItem(k) for k in self.time_bank.keys() if self.time_bank.get(k, 0) > 0]

    def on_timer_tick(self):
        if not self.active_task: return
        tk = self.active_task; tk.elapsed_seconds += 1
        m, s = divmod(tk.elapsed_seconds, 60); self.label_task_time.setText(f"计时: {m:02d}:{s:02d}")
        ts = tk.target_min * 60
        if ts > 0:
            p = min(100, int((tk.elapsed_seconds / ts) * 100)); self.progress_bar.setValue(p)
            for mil in [0, 20, 40, 60, 80]:
                if p >= mil and tk.last_milestone <= mil:
                    rew = tk.base_points * 0.1; self.total_points += rew; tk.process_points_earned += rew
                    tk.last_milestone = mil + 1; self.add_log("任务", f"{tk.name}({mil}%)", rew); self.update_all_ui()
            self.label_reward_info.setText(f"已领奖励: {round(tk.process_points_earned,1)} / 总分: {tk.base_points}")

    def refresh_display_on_click(self, item):
        for lw in self.task_lists.values():
            if lw != self.sender(): lw.clearSelection(); lw.setCurrentItem(None)
        if self.main_timer.isActive(): return
        tk = item.data(Qt.UserRole); self.active_task = tk
        m, s = divmod(tk.elapsed_seconds, 60); self.label_task_time.setText(f"计时: {m:02d}:{s:02d}")
        ts = tk.target_min * 60; pct = (tk.elapsed_seconds / ts * 100) if ts > 0 else 0
        self.progress_bar.setValue(int(pct)); self.label_reward_info.setText(f"已领奖励: {round(tk.process_points_earned,1)} / 总分: {tk.base_points}")

    def toggle_task_timer(self):
        if not self.active_task: return
        if self.main_timer.isActive(): self.main_timer.stop(); self.btn_s.setText("▶️ 开始计时")
        else: self.main_timer.start(1000); self.btn_s.setText("⏸️ 暂停")

    def finish_task(self):
        if not self.active_task: return
        tk = self.active_task; self.main_timer.stop()
        rem = max(0, tk.base_points - tk.process_points_earned)
        self.total_points += rem; tk.current_daily += 1; tk.last_date = datetime.now().strftime("%Y-%m-%d")
        if "一次性" in tk.task_type or tk.current_daily >= tk.max_daily: tk.is_completed = True
        self.add_log("任务", f"{tk.name}(结算)", rem); self.refresh_task_lists(); self.update_all_ui(); self.save_data()

    def add_log(self, t, n, p): self.history_logs.append({"time": datetime.now(), "type": t, "name": n, "points": p})

    def refresh_task_lists(self):
        for lw in self.task_lists.values(): lw.clear()
        for t in self.all_tasks:
            it = QListWidgetItem()
            it.setData(Qt.UserRole, t)
            
            # 1. 组装文字内容
            lim = f"({t.current_daily}/{t.max_daily})" if "一次性" not in t.task_type else ""
            deadline = f" [⏰{t.checkin_time}]" if t.checkin_time else ""
            text = f"{'✅' if t.is_completed else '🕒'} {t.name}{lim}{deadline}"
            
            # 2. 创建一个支持换行的 Label 作为显示控件
            lbl = QLabel(text)
            lbl.setWordWrap(True)  # 开启自动换行
            lbl.setContentsMargins(5, 5, 5, 5) # 留点边距更好看
            
            # 3. 将 Label 塞进列表项中
            target_lw = self.task_lists["一次性" if "一次性" in t.task_type else ("定时签到" if "签" in t.task_type else "常规任务")]
            if t.is_completed: target_lw = self.task_lists["已完成"]
            
            target_lw.addItem(it)
            target_lw.setItemWidget(it, lbl) # 核心：用 Label 替换默认渲染
            
            # 4. 自动调整高度以适应换行后的文字
            it.setSizeHint(lbl.sizeHint())
    def show_task_menu(self, pos):
        lw = self.sender(); item = lw.itemAt(pos)
        if item:
            m = QMenu(); d = m.addAction("🗑️ 删除")
            if m.exec(lw.mapToGlobal(pos)) == d: self.all_tasks.remove(item.data(Qt.UserRole)); self.refresh_task_lists(); self.save_data()

    def auto_check_reset(self):
        today = datetime.now().strftime("%Y-%m-%d"); ch = False
        for t in self.all_tasks:
            if "一次性" not in t.task_type and t.last_date != today:
                t.current_daily = 0; t.is_completed = False; t.elapsed_seconds = 0; t.process_points_earned = 0; t.last_milestone = 0; t.last_date = today; ch = True
        if ch: self.refresh_task_lists(); self.save_data()

    def create_store_tab(self):
        tab = QWidget(); layout = QVBoxLayout(tab)
        h = QHBoxLayout(); self.s_n = QLineEdit(); self.s_p = QLineEdit(); self.s_m = QLineEdit()
        self.s_n.setPlaceholderText("项目"); self.s_p.setPlaceholderText("分"); self.s_m.setPlaceholderText("分钟")
        btn = QPushButton("上架"); btn.clicked.connect(self.add_store_item)
        h.addWidget(self.s_n); h.addWidget(self.s_p); h.addWidget(self.s_m); h.addWidget(btn); layout.addLayout(h)
        self.store_list = QListWidget(); self.store_list.itemClicked.connect(self.buy_store_item)
        layout.addWidget(QLabel("🛒 商店:")); layout.addWidget(self.store_list)
        self.bank_display = QLabel("时长余额: 空"); layout.addWidget(self.bank_display)
        self.consume_list = QListWidget(); self.consume_list.itemClicked.connect(self.start_consume_logic)
        layout.addWidget(QLabel("🚀 开启娱乐 (边玩边生利息):")); layout.addWidget(self.consume_list)
        self.label_s_status = QLabel("状态: 闲置")
        btn_stop = QPushButton("停止计时"); btn_stop.clicked.connect(self.stop_consuming)
        layout.addWidget(self.label_s_status); layout.addWidget(btn_stop)
        self.tab_widget.addTab(tab, "娱乐商店")

    def add_store_item(self):
        n, p, m = self.s_n.text(), int(self.s_p.text() or 0), int(self.s_m.text() or 0)
        if n: it = QListWidgetItem(f"🎁 {n} | {p}分 | {m}分"); it.setData(Qt.UserRole, {"name": n, "pts": p, "min": m}); self.store_list.addItem(it); self.save_data()

    def buy_store_item(self, item):
        d = item.data(Qt.UserRole)
        if self.total_points >= d["pts"]:
            self.total_points -= d["pts"]; self.time_bank[d["name"]] = self.time_bank.get(d["name"], 0) + d["min"] * 60
            self.add_log("支出", f"购买:{d['name']}", -d["pts"]); self.update_all_ui(); self.save_data()

    def start_consume_logic(self, item):
        if self.time_bank.get(item.text(), 0) > 0: self.act_c = item.text(); self.store_timer.start(1000)

    def stop_consuming(self): self.store_timer.stop(); self.act_c = None; self.label_s_status.setText("状态: 闲置")

    def create_reward_tab(self):
        tab = QWidget(); layout = QVBoxLayout(tab)
        h = QHBoxLayout(); self.r_n = QLineEdit(); self.r_p = QLineEdit()
        btn = QPushButton("上架奖品"); btn.clicked.connect(self.add_reward_item)
        h.addWidget(self.r_n); h.addWidget(self.r_p); h.addWidget(btn); layout.addLayout(h)
        lh = QHBoxLayout()
        v1 = QVBoxLayout(); v1.addWidget(QLabel("🏆 待兑换:")); self.reward_list = QListWidget()
        self.reward_list.itemClicked.connect(self.redeem_reward); v1.addWidget(self.reward_list)
        v2 = QVBoxLayout(); v2.addWidget(QLabel("🎁 已领取 (右键退货):")); self.purchased_list = QListWidget()
        self.purchased_list.setContextMenuPolicy(Qt.CustomContextMenu); self.purchased_list.customContextMenuRequested.connect(self.show_reward_refund_menu)
        v2.addWidget(self.purchased_list); lh.addLayout(v1); lh.addLayout(v2); layout.addLayout(lh)
        self.tab_widget.addTab(tab, "实物奖励")

    def add_reward_item(self):
        n, p = self.r_n.text(), int(self.r_p.text() or 0)
        if n: it = QListWidgetItem(f"🏆 {n} | {p}分"); it.setData(Qt.UserRole, {"name": n, "pts": p}); self.reward_list.addItem(it); self.save_data()

    def redeem_reward(self, item):
        d = item.data(Qt.UserRole)
        if self.total_points >= d["pts"]:
            self.total_points -= d["pts"]; self.reward_list.takeItem(self.reward_list.row(item))
            nit = QListWidgetItem(f"🎁 {d['name']} (已兑换)"); nit.setData(Qt.UserRole, d); self.purchased_list.addItem(nit)
            self.add_log("实物", f"兑换:{d['name']}", -d["pts"]); self.update_all_ui(); self.save_data()

    def show_reward_refund_menu(self, pos):
        it = self.purchased_list.itemAt(pos)
        if it:
            m = QMenu(); rf = m.addAction("💰 退货返款")
            if m.exec(self.purchased_list.mapToGlobal(pos)) == rf:
                d = it.data(Qt.UserRole); self.total_points += d["pts"]; self.purchased_list.takeItem(self.purchased_list.row(it))
                sit = QListWidgetItem(f"🏆 {d['name']} | {d['pts']}分"); sit.setData(Qt.UserRole, d); self.reward_list.addItem(sit)
                self.add_log("退货", f"退还:{d['name']}", d["pts"]); self.update_all_ui(); self.save_data()

    def create_stat_tab(self):
        tab = QWidget(); layout = QVBoxLayout(tab)
        h = QHBoxLayout(); self.year_combo = QComboBox()
        for y in range(2025, 2031): self.year_combo.addItem(f"{y}年", y)
        self.year_combo.setCurrentIndex(self.year_combo.findData(2026) or 0)
        self.month_combo = QComboBox()
        for i in range(1, 13): self.month_combo.addItem(f"{i}月", i)
        self.month_combo.setCurrentIndex(datetime.now().month - 1)
        btn = QPushButton("查询"); btn.clicked.connect(self.refresh_stats)
        h.addWidget(self.year_combo); h.addWidget(self.month_combo); h.addWidget(btn); layout.addLayout(h)
        self.stat_log_list = QListWidget(); self.lbl_month_total = QLabel("本月任务收益: 0")
        layout.addWidget(self.lbl_month_total); layout.addWidget(self.stat_log_list)
        self.tab_widget.addTab(tab, "历史记录")

    def refresh_stats(self):
        self.stat_log_list.clear(); g = 0
        sy = self.year_combo.currentData(); sm = self.month_combo.currentData()
        for l in reversed(self.history_logs):
            lt = l["time"]
            if lt.year == sy and lt.month == sm:
                p = l["points"]; it = QListWidgetItem(f"[{lt.strftime('%Y-%m-%d %H:%M')}] {l['name']} = {p}")
                if p < 0: it.setForeground(Qt.red)
                self.stat_log_list.addItem(it)
                if l.get('type') == "任务": g += p
        self.lbl_month_total.setText(f"{sy}年{sm}月 任务收益: {round(g, 1)}")

if __name__ == "__main__":
    app = QApplication(sys.argv); window = LearningApp(); window.show(); sys.exit(app.exec())
