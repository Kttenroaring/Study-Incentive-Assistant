# -*- coding: utf-8 -*-
import sys
import pickle
import os
from datetime import datetime
from PySide6.QtWidgets import (QApplication, QMainWindow, QTabWidget, 
                               QWidget, QVBoxLayout, QLabel, QPushButton, 
                               QLineEdit, QHBoxLayout, QListWidget, QMessageBox, 
                               QListWidgetItem, QRadioButton, QButtonGroup, 
                               QMenu, QComboBox)
from PySide6.QtCore import Qt, QTimer

# --- 核心任务类 ---
class Task:
    def __init__(self, name, task_type, target_min, base_points, max_daily=1):
        self.name = name
        self.task_type = task_type
        self.target_min = target_min
        self.base_points = base_points
        self.max_daily = max_daily
        self.current_daily = 0  
        self.last_date = datetime.now().strftime("%Y-%m-%d")
        self.elapsed_seconds = 0
        self.is_completed = False

class LearningApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("学习积分助手 v2.1 - 四分区精准匹配版")
        
        self.data_file = "learning_data.dat"
        self.total_points = 0
        self.all_tasks = []      # 数据总仓库
        self.time_bank = {}      # 时长银行
        self.history_logs = []   # 历史记录
        self.last_interest_date = ""
        self.active_consume_type = None

        self.init_ui()
        self.load_data()

        self.main_timer = QTimer(); self.main_timer.timeout.connect(self.on_timer_tick)
        self.store_timer = QTimer(); self.store_timer.timeout.connect(self.update_store_timer)

    # --- 第一部分：UI 构建 ---
    def init_ui(self):
        self.setGeometry(100, 100, 1150, 850)
        self.central_widget = QWidget(); self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        # 积分显示
        self.points_label = QLabel(f"💰 当前总积分: {self.total_points}")
        self.points_label.setStyleSheet("font-size: 26px; color: #E67E22; font-weight: bold; padding: 10px;")
        self.main_layout.addWidget(self.points_label)

        self.tab_widget = QTabWidget(); self.main_layout.addWidget(self.tab_widget)

        self.create_task_tab()
        self.create_store_tab()
        self.create_reward_tab()
        self.create_stat_tab()

    def create_task_tab(self):
        tab = QWidget(); layout = QVBoxLayout(tab)
        
        # 输入区
        h1 = QHBoxLayout()
        self.t_name_in = QLineEdit(); self.t_name_in.setPlaceholderText("任务名称")
        self.t_min_in = QLineEdit(); self.t_min_in.setPlaceholderText("分钟")
        self.t_pts_in = QLineEdit(); self.t_pts_in.setPlaceholderText("积分")
        h1.addWidget(self.t_name_in); h1.addWidget(self.t_min_in); h1.addWidget(self.t_pts_in)
        
        h2 = QHBoxLayout()
        self.t_type_group = QButtonGroup(self)
        self.r1 = QRadioButton("一次性"); self.r1.setChecked(True); self.t_type_group.addButton(self.r1, 0)
        self.r2 = QRadioButton("常规任务"); self.t_type_group.addButton(self.r2, 1)
        self.r3 = QRadioButton("定时签到"); self.t_type_group.addButton(self.r3, 2)
        self.t_limit_in = QLineEdit(); self.t_limit_in.setText("1"); self.t_limit_in.setFixedWidth(50)
        btn_add = QPushButton("➕ 添加任务"); btn_add.clicked.connect(self.add_task)
        h2.addWidget(self.r1); h2.addWidget(self.r2); h2.addWidget(self.r3); h2.addWidget(QLabel("上限:")); h2.addWidget(self.t_limit_in); h2.addWidget(btn_add)
        layout.addLayout(h1); layout.addLayout(h2)

        # 四分区显示区 (核心逻辑：Key 必须与 RadioButton 完全一致)
        lists_h = QHBoxLayout()
        self.task_lists = {
            "一次性": QListWidget(), 
            "常规任务": QListWidget(), 
            "定时签到": QListWidget(), 
            "已完成": QListWidget()
        }
        for name, lw in self.task_lists.items():
            box = QVBoxLayout(); lbl = QLabel(name); lbl.setAlignment(Qt.AlignCenter)
            lbl.setStyleSheet("background:#ECF0F1; font-weight:bold; padding:5px; border:1px solid #BDC3C7;")
            lw.setContextMenuPolicy(Qt.CustomContextMenu); lw.customContextMenuRequested.connect(self.show_task_menu)
            box.addWidget(lbl); box.addWidget(lw); lists_h.addLayout(box)
        layout.addLayout(lists_h)

        # 计时控制
        ctrl = QHBoxLayout()
        self.label_task_time = QLabel("计时: 00:00")
        self.label_task_time.setStyleSheet("font-size: 18px; color: #E74C3C; font-family: Consolas;")
        btn_s = QPushButton("开始/暂停"); btn_s.clicked.connect(self.toggle_task_timer)
        btn_f = QPushButton("结算任务"); btn_f.clicked.connect(self.finish_task)
        ctrl.addWidget(self.label_task_time); ctrl.addStretch(); ctrl.addWidget(btn_s); ctrl.addWidget(btn_f)
        layout.addLayout(ctrl); self.tab_widget.addTab(tab, "学习任务")

    # --- 第二部分：核心分拣逻辑 (解决定时签到显示问题) ---
    def refresh_task_lists(self):
        """核心修复：使用模糊匹配确保旧数据也能正确分类"""
        for lw in self.task_lists.values(): lw.clear()
        for task in self.all_tasks:
            item = QListWidgetItem()
            item.setData(Qt.UserRole, task)
            self.update_task_display(item, task)
            
            if task.is_completed:
                self.task_lists["已完成"].addItem(item)
            else:
                t_type = task.task_type.strip()
                # --- 强制校准逻辑 ---
                if "一次性" in t_type:
                    self.task_lists["一次性"].addItem(item)
                elif "签" in t_type: # 只要包含"签"字就进去
                    self.task_lists["定时签到"].addItem(item)
                else:
                    self.task_lists["常规任务"].addItem(item)

    # --- 第三部分：还原「利息版」的统计逻辑 ---
    def create_stat_tab(self):
        tab = QWidget(); layout = QVBoxLayout(tab)
        h = QHBoxLayout()
        self.year_combo = QComboBox(); self.year_combo.addItem("2026")
        self.month_combo = QComboBox()
        for i in range(1, 13): self.month_combo.addItem(f"{i}月", i)
        self.month_combo.setCurrentIndex(datetime.now().month - 1)
        btn = QPushButton("刷新统计"); btn.clicked.connect(self.refresh_stats)
        h.addWidget(self.year_combo); h.addWidget(self.month_combo); h.addWidget(btn)
        layout.addLayout(h)
        
        self.stat_log_list = QListWidget()
        self.lbl_month_total = QLabel("本月收益: 0 分")
        self.lbl_month_total.setStyleSheet("font-size: 18px; color: #27AE60; font-weight: bold;")
        layout.addWidget(self.lbl_month_total); layout.addWidget(self.stat_log_list)
        self.tab_widget.addTab(tab, "统计成果")

    def refresh_stats(self):
        """还原自「利息版.txt」：仅计算 type 为 '任务' 的积分作为收益"""
        self.stat_log_list.clear()
        selected_month = self.month_combo.currentData()
        gain = 0
        for log in reversed(self.history_logs):
            log_time = log["time"]
            if log_time.month == selected_month:
                pts = log["points"]
                it = QListWidgetItem(f"[{log_time.strftime('%m-%d %H:%M')}] {log['name']}: {pts}")
                # 负数变红
                if pts < 0: it.setForeground(Qt.red)
                self.stat_log_list.addItem(it)
                
                # 只有类型是"任务"的才计入月收益
                if log.get('type') == "任务":
                    gain += pts
        self.lbl_month_total.setText(f"本月收益: {round(gain, 2)} 分")

    # --- 第四部分：功能完整回归 (实物奖励、利息、退货) ---
    def calculate_interest(self):
        """0.1% 复利结息逻辑"""
        today_str = datetime.now().date().strftime("%Y-%m-%d")
        if not self.last_interest_date: self.last_interest_date = today_str; return
        last_dt = datetime.strptime(self.last_interest_date, "%Y-%m-%d").date()
        days = (datetime.now().date() - last_dt).days
        if days > 0:
            earned = self.total_points * 0.001 * days # 0.1% 利率
            if earned > 0:
                self.total_points += earned
                self.add_log("利息", f"{days}天结息", round(earned, 4))
            self.last_interest_date = today_str; self.save_data()

    def show_task_menu(self, pos):
        lw = self.sender(); item = lw.itemAt(pos)
        if not item: return
        menu = QMenu(); del_act = menu.addAction("🗑️ 删除任务")
        if menu.exec(lw.mapToGlobal(pos)) == del_act:
            task = item.data(Qt.UserRole)
            if task in self.all_tasks: self.all_tasks.remove(task)
            self.refresh_task_lists(); self.save_data()

    # --- 辅助函数 ---
    def add_task(self):
        n = self.t_name_in.text(); m = int(self.t_min_in.text() or 0)
        p = int(self.t_pts_in.text() or 0); lim = int(self.t_limit_in.text() or 1)
        if not n: return
        tp = ["一次性", "常规任务", "定时签到"][self.t_type_group.checkedId()]
        self.all_tasks.append(Task(n, tp, m, p, max_daily=lim))
        self.refresh_task_lists(); self.save_data(); self.t_name_in.clear()

    def finish_task(self):
        item = self.get_current_task_item()
        if not item: return
        task = item.data(Qt.UserRole)
        if task.is_completed: return
        self.total_points += task.base_points
        task.current_daily += 1
        if task.task_type == "一次性" or task.current_daily >= task.max_daily: task.is_completed = True
        self.add_log("任务", task.name, task.base_points)
        self.refresh_task_lists(); self.update_all_ui(); self.save_data()

    def get_current_task_item(self):
        for lw in self.task_lists.values():
            if lw.currentItem(): return lw.currentItem()
        return None

    def add_log(self, t, n, p): 
        self.history_logs.append({"time": datetime.now(), "type": t, "name": n, "points": p})
        self.refresh_stats()

    def update_task_display(self, item, task):
        lim = f"({task.current_daily}/{task.max_daily})" if task.task_type != "一次性" else ""
        item.setText(f"{'✅' if task.is_completed else '🕒'} {task.name} {lim}")
        item.setForeground(Qt.gray if task.is_completed else Qt.black)

    def update_all_ui(self):
        self.points_label.setText(f"💰 当前总积分: {round(self.total_points, 2)}")
        b = [f"{k}:{v//60}分" for k, v in self.time_bank.items() if v > 0]
        self.bank_display.setText("余额: " + (" | ".join(b) if b else "空"))
        self.consume_list.clear()
        for k in self.time_bank.keys(): self.consume_list.addItem(k)

    # --- 其他原有功能逻辑 ---
    def create_store_tab(self):
        tab = QWidget(); layout = QVBoxLayout(tab)
        h = QHBoxLayout()
        self.s_n = QLineEdit(); self.s_p = QLineEdit(); self.s_m = QLineEdit()
        self.s_n.setPlaceholderText("商品名"); self.s_p.setPlaceholderText("积分"); self.s_m.setPlaceholderText("分钟")
        btn = QPushButton("上架"); btn.clicked.connect(self.add_store_item)
        h.addWidget(self.s_n); h.addWidget(self.s_p); h.addWidget(self.s_m); h.addWidget(btn); layout.addLayout(h)
        self.store_list = QListWidget(); self.store_list.itemClicked.connect(self.buy_store_item)
        layout.addWidget(QLabel("🛒 点击购买:")); layout.addWidget(self.store_list)
        self.bank_display = QLabel("余额: 空"); layout.addWidget(self.bank_display)
        self.consume_list = QListWidget(); self.consume_list.itemClicked.connect(self.start_consume_logic)
        self.consume_list.setContextMenuPolicy(Qt.CustomContextMenu); self.consume_list.customContextMenuRequested.connect(self.show_refund_menu)
        layout.addWidget(QLabel("🚀 点击消费 (右键退换):")); layout.addWidget(self.consume_list)
        self.label_s_status = QLabel("状态: 闲置"); btn_stop = QPushButton("停止"); btn_stop.clicked.connect(self.stop_consuming)
        layout.addWidget(self.label_s_status); layout.addWidget(btn_stop); self.tab_widget.addTab(tab, "时长商店")

    def create_reward_tab(self):
        tab = QWidget(); layout = QVBoxLayout(tab)
        h = QHBoxLayout(); self.r_n = QLineEdit(); self.r_p = QLineEdit()
        self.r_n.setPlaceholderText("奖品名称"); self.r_p.setPlaceholderText("积分")
        btn = QPushButton("上架实物"); btn.clicked.connect(self.add_reward_item)
        h.addWidget(self.r_n); h.addWidget(self.r_p); h.addWidget(btn); layout.addLayout(h)
        self.reward_list = QListWidget(); self.reward_list.itemClicked.connect(self.redeem_reward)
        layout.addWidget(self.reward_list); self.tab_widget.addTab(tab, "实物奖励")

    def add_reward_item(self):
        n = self.r_n.text(); p = int(self.r_p.text() or 0)
        if n:
            it = QListWidgetItem(f"🏆 {n} | {p}分"); it.setData(Qt.UserRole, {"name": n, "pts": p})
            self.reward_list.addItem(it); self.r_n.clear(); self.save_data()

    def redeem_reward(self, item):
        d = item.data(Qt.UserRole)
        if self.total_points >= d["pts"]:
            self.total_points -= d["pts"]; self.add_log("实物", f"领取:{d['name']}", -d["pts"])
            self.update_all_ui(); self.save_data()
            QMessageBox.information(self, "成功", f"兑换【{d['name']}】成功！")

    def add_store_item(self):
        n = self.s_n.text(); p = int(self.s_p.text() or 0); m = int(self.s_m.text() or 0)
        if n:
            it = QListWidgetItem(f"🎁 {n} | {p}分 | {m}分钟")
            it.setData(Qt.UserRole, {"name": n, "pts": p, "min": m})
            self.store_list.addItem(it); self.s_n.clear(); self.save_data()

    def buy_store_item(self, item):
        d = item.data(Qt.UserRole)
        if self.total_points >= d["pts"]:
            self.total_points -= d["pts"]; self.time_bank[d["name"]] = self.time_bank.get(d["name"], 0) + d["min"] * 60
            self.add_log("支出", f"购买:{d['name']}", -d["pts"]); self.update_all_ui(); self.save_data()

    def show_refund_menu(self, pos):
        lw = self.sender(); item = lw.itemAt(pos)
        if not item: return
        menu = QMenu(); refund_act = menu.addAction("💰 退货")
        if menu.exec(lw.mapToGlobal(pos)) == refund_act:
            name = item.text(); refund_pts = 0
            for log in reversed(self.history_logs):
                if log["type"] == "支出" and name in log["name"]: refund_pts = abs(log["points"]); break
            if refund_pts > 0: self.total_points += refund_pts
            if name in self.time_bank: del self.time_bank[name]
            self.add_log("退货", f"退还:{name}", refund_pts); self.update_all_ui(); self.save_data()

    def start_consume_logic(self, item):
        n = item.text()
        if self.time_bank.get(n, 0) > 0: self.active_consume_type = n; self.store_timer.start(1000)

    def update_store_timer(self):
        c = self.active_consume_type
        if c and self.time_bank.get(c, 0) > 0:
            self.time_bank[c] -= 1; m, s = divmod(self.time_bank[c], 60)
            self.label_s_status.setText(f"🔥 {c} 剩余: {m:02d}:{s:02d}")
        else: self.stop_consuming()

    def stop_consuming(self):
        self.store_timer.stop(); self.active_consume_type = None; self.label_s_status.setText("状态: 闲置")

    def on_timer_tick(self):
        item = self.get_current_task_item()
        if item:
            tk = item.data(Qt.UserRole)
            if not tk.is_completed:
                tk.elapsed_seconds += 1; m, s = divmod(tk.elapsed_seconds, 60)
                self.label_task_time.setText(f"计时: {m:02d}:{s:02d}")

    def toggle_task_timer(self):
        if self.main_timer.isActive(): self.main_timer.stop()
        else: self.main_timer.start(1000)

    def load_data(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "rb") as f:
                    d = pickle.load(f)
                    self.total_points = d.get("points", 0); self.all_tasks = d.get("tasks", [])
                    self.time_bank = d.get("bank", {}); self.history_logs = d.get("logs", [])
                    self.last_interest_date = d.get("last_interest_date", "")
                    self.calculate_interest(); self.refresh_task_lists(); self.update_all_ui()
            except: pass

    def save_data(self):
        with open(self.data_file, "wb") as f:
            pickle.dump({"points": self.total_points, "tasks": self.all_tasks, "bank": self.time_bank, "logs": self.history_logs, "last_interest_date": self.last_interest_date}, f)

if __name__ == "__main__":
    app = QApplication(sys.argv); window = LearningApp(); window.show(); sys.exit(app.exec())
