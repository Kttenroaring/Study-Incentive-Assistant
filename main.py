# -*- coding: utf-8 -*-
import sys
import pickle
import os
from datetime import datetime, timedelta
from PySide6.QtWidgets import (QApplication, QMainWindow, QTabWidget, 
                               QWidget, QVBoxLayout, QLabel, QPushButton, 
                               QLineEdit, QHBoxLayout, QListWidget, QMessageBox, 
                               QInputDialog, QListWidgetItem, QRadioButton, QButtonGroup, 
                               QMenu, QComboBox)
from PySide6.QtCore import Qt, QTimer, QTime

# 任务类支持序列化
class Task:
    def __init__(self, name, task_type, target_min, base_points, checkin_time=""):
        self.name = name
        self.task_type = task_type
        self.target_min = target_min
        self.base_points = base_points
        self.checkin_time = checkin_time
        self.elapsed_seconds = 0
        self.is_completed = False

class LearningApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("学习积分助手 v1.5 - 自动存档版")
        self.data_file = "learning_data.dat"
        
        # 默认初始化数据
        self.total_points = 0
        self.time_bank = {} 
        self.history_logs = []
        self.tasks_data = [] # 存储原始任务数据用于存档
        self.active_consume_type = None

        # 尝试加载存档
        self.load_data()

        self.main_timer = QTimer()
        self.main_timer.timeout.connect(self.on_timer_tick)
        self.store_timer = QTimer()
        self.store_timer.timeout.connect(self.update_store_timer)

        self.init_ui()

    # --- 存档功能 ---
    def save_data(self):
        try:
            # 提取任务列表中的任务对象
            current_tasks = []
            for i in range(self.task_list.count()):
                current_tasks.append(self.task_list.item(i).data(Qt.UserRole))
            
            data = {
                "points": self.total_points,
                "bank": self.time_bank,
                "logs": self.history_logs,
                "tasks": current_tasks
            }
            with open(self.data_file, "wb") as f:
                pickle.dump(data, f)
        except Exception as e:
            print(f"存档失败: {e}")

    def load_data(self):
        if os.path.exists(self.data_file):
            try:
                with open(self.data_file, "rb") as f:
                    data = pickle.load(f)
                    self.total_points = data.get("points", 0)
                    self.time_bank = data.get("bank", {})
                    self.history_logs = data.get("logs", [])
                    self.tasks_data = data.get("tasks", [])
            except Exception as e:
                print(f"读取存档失败: {e}")

    def init_ui(self):
        self.setGeometry(100, 100, 1150, 850)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        self.points_label = QLabel(f"💰 当前总积分: {self.total_points}")
        self.points_label.setStyleSheet("font-size: 26px; color: #E67E22; font-weight: bold; padding: 10px;")
        self.main_layout.addWidget(self.points_label)

        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget)

        self.create_task_tab()
        self.create_store_tab()
        self.create_reward_tab()
        self.create_stat_tab()
        
        # 加载任务到列表
        for t in self.tasks_data:
            item = QListWidgetItem(f"[{t.task_type}] {t.name} ({t.base_points}分)")
            if t.is_completed: 
                item.setText(f"✅ {t.name} (已完成)")
                item.setForeground(Qt.gray)
            item.setData(Qt.UserRole, t)
            self.task_list.addItem(item)
        
        # 更新银行显示
        self.update_all_ui()

    def create_task_tab(self):
        tab = QWidget(); layout = QVBoxLayout(tab)
        add_box = QVBoxLayout()
        h1 = QHBoxLayout()
        self.t_name_in = QLineEdit(); self.t_name_in.setPlaceholderText("任务名")
        self.t_min_in = QLineEdit(); self.t_min_in.setPlaceholderText("预计分钟")
        self.t_pts_in = QLineEdit(); self.t_pts_in.setPlaceholderText("积分")
        h1.addWidget(self.t_name_in); h1.addWidget(self.t_min_in); h1.addWidget(self.t_pts_in)
        h2 = QHBoxLayout()
        self.t_type_group = QButtonGroup(self)
        self.r1 = QRadioButton("一次性"); self.r1.setChecked(True); self.t_type_group.addButton(self.r1, 0)
        self.r2 = QRadioButton("常规"); self.t_type_group.addButton(self.r2, 1)
        self.r3 = QRadioButton("签到"); self.t_type_group.addButton(self.r3, 2)
        self.checkin_in = QLineEdit(); self.checkin_in.setPlaceholderText("签到截止(如 08:30)")
        btn_add = QPushButton("➕ 添加任务"); btn_add.clicked.connect(self.add_task)
        h2.addWidget(self.r1); h2.addWidget(self.r2); h2.addWidget(self.r3); h2.addWidget(self.checkin_in); h2.addWidget(btn_add)
        add_box.addLayout(h1); add_box.addLayout(h2); layout.addLayout(add_box)
        self.task_list = QListWidget(); self.task_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.task_list.customContextMenuRequested.connect(lambda p: self.show_del_menu(self.task_list, p))
        layout.addWidget(self.task_list)
        ctrl = QHBoxLayout()
        self.label_task_time = QLabel("用时: 00:00")
        btn_start = QPushButton("开始/暂停"); btn_start.clicked.connect(self.toggle_task_timer)
        btn_manual = QPushButton("补录"); btn_manual.clicked.connect(self.manual_record)
        btn_finish = QPushButton("结算/打卡"); btn_finish.clicked.connect(self.finish_task)
        ctrl.addWidget(self.label_task_time); ctrl.addWidget(btn_start); ctrl.addWidget(btn_manual); ctrl.addWidget(btn_finish)
        layout.addLayout(ctrl); self.tab_widget.addTab(tab, "学习任务")

    def create_store_tab(self):
        tab = QWidget(); layout = QVBoxLayout(tab)
        add_box = QHBoxLayout()
        self.s_name_in = QLineEdit(); self.s_name_in.setPlaceholderText("商品名"); self.s_pts_in = QLineEdit(); self.s_pts_in.setPlaceholderText("价格"); self.s_min_in = QLineEdit(); self.s_min_in.setPlaceholderText("分钟")
        btn_s_add = QPushButton("上架"); btn_s_add.clicked.connect(self.add_store_item)
        add_box.addWidget(self.s_name_in); add_box.addWidget(self.s_pts_in); add_box.addWidget(self.s_min_in); add_box.addWidget(btn_s_add); layout.addLayout(add_box)
        self.store_list = QListWidget(); self.store_list.itemClicked.connect(self.buy_store_item)
        self.store_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.store_list.customContextMenuRequested.connect(lambda p: self.show_del_menu(self.store_list, p))
        layout.addWidget(QLabel("🛒 点击购买时长:")); layout.addWidget(self.store_list)
        self.bank_display = QLabel("银行余额: 空"); self.bank_display.setStyleSheet("background:#eee; padding:10px;")
        layout.addWidget(self.bank_display)
        self.consume_list = QListWidget(); self.consume_list.itemClicked.connect(self.start_consume_logic)
        for k in self.time_bank.keys(): self.consume_list.addItem(k)
        layout.addWidget(QLabel("🚀 点击下方种类开始消费:")); layout.addWidget(self.consume_list)
        self.label_s_status = QLabel("状态: 闲置")
        btn_stop = QPushButton("⏹️ 停止消费"); btn_stop.clicked.connect(self.stop_consuming)
        layout.addWidget(self.label_s_status); layout.addWidget(btn_stop); self.tab_widget.addTab(tab, "时长商店")

    def create_reward_tab(self):
        tab = QWidget(); layout = QVBoxLayout(tab)
        add_box = QHBoxLayout()
        self.r_name_in = QLineEdit(); self.r_name_in.setPlaceholderText("奖励名"); self.r_pts_in = QLineEdit(); self.r_pts_in.setPlaceholderText("积分")
        btn_r_add = QPushButton("上架奖励"); btn_r_add.clicked.connect(self.add_reward_item)
        add_box.addWidget(self.r_name_in); add_box.addWidget(self.r_pts_in); add_box.addWidget(btn_r_add); layout.addLayout(add_box)
        self.reward_list = QListWidget(); self.reward_list.itemClicked.connect(self.buy_reward_direct)
        self.reward_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.reward_list.customContextMenuRequested.connect(lambda p: self.show_del_menu(self.reward_list, p))
        layout.addWidget(QLabel("🎁 实物奖励:")); layout.addWidget(self.reward_list)
        self.history_list = QListWidget(); layout.addWidget(QLabel("✅ 领用记录:")); layout.addWidget(self.history_list)
        self.tab_widget.addTab(tab, "购物奖励")

    def create_stat_tab(self):
        tab = QWidget(); layout = QVBoxLayout(tab)
        filter_box = QHBoxLayout()
        filter_box.addWidget(QLabel("📅 选择查看历史："))
        self.year_combo = QComboBox()
        curr_year = datetime.now().year
        for y in range(2026, curr_year + 5): self.year_combo.addItem(str(y))
        self.month_combo = QComboBox()
        for m in range(1, 13): self.month_combo.addItem(f"{m}月", m)
        self.month_combo.setCurrentIndex(datetime.now().month - 1)
        btn_query = QPushButton("🔍 刷新查询"); btn_query.clicked.connect(self.refresh_stats)
        filter_box.addWidget(self.year_combo); filter_box.addWidget(self.month_combo); filter_box.addWidget(btn_query); filter_box.addStretch()
        layout.addLayout(filter_box)
        self.lbl_month_total = QLabel("该月累计收益: 0 分")
        self.lbl_month_total.setStyleSheet("font-size: 20px; font-weight: bold; color: #16A085; background: #E8F8F5; padding: 15px;")
        layout.addWidget(self.lbl_month_total)
        log_layout = QHBoxLayout()
        v1 = QVBoxLayout(); v1.addWidget(QLabel("📜 任务记录:")); self.log_tasks = QListWidget(); v1.addWidget(self.log_tasks)
        v2 = QVBoxLayout(); v2.addWidget(QLabel("💸 收支明细:")); self.log_points = QListWidget(); v2.addWidget(self.log_points)
        log_layout.addLayout(v1); log_layout.addLayout(v2); layout.addLayout(log_layout)
        self.tab_widget.addTab(tab, "统计成果")

    # --- 核心逻辑 (触发自动存档) ---
    def add_log(self, l_type, name, points, duration=0):
        log = {"time": datetime.now(), "type": l_type, "name": name, "points": points, "duration": duration}
        self.history_logs.append(log)
        self.save_data() # 存档
        self.refresh_stats()

    def finish_task(self):
        item = self.task_list.currentItem()
        if not item: return
        task = item.data(Qt.UserRole)
        if task.is_completed: return
        self.main_timer.stop()
        earned = 0; actual_min = task.elapsed_seconds // 60
        if task.task_type == "签到":
            if QTime.currentTime() <= QTime.fromString(task.checkin_time, "HH:mm"): earned = task.base_points
            else: QMessageBox.warning(self, "失败", "签到超时！"); return
        else: earned = task.base_points + max(0, task.target_min - actual_min)
        self.total_points += earned
        self.add_log("任务", task.name, earned, actual_min)
        if task.task_type == "一次性":
            task.is_completed = True; item.setText(f"✅ {task.name} (+{earned})"); item.setForeground(Qt.gray)
        else: task.elapsed_seconds = 0; QMessageBox.information(self, "成功", f"获得 {earned} 积分！")
        self.update_all_ui(); self.save_data()

    def add_task(self):
        name = self.t_name_in.text(); t_min = int(self.t_min_in.text() or 0); b_pts = int(self.t_pts_in.text() or 0)
        task = Task(name, ["一次性", "常规", "签到"][self.t_type_group.checkedId()], t_min, b_pts, self.checkin_in.text())
        item = QListWidgetItem(f"[{task.task_type}] {name} ({b_pts}分)"); item.setData(Qt.UserRole, task)
        self.task_list.addItem(item); self.t_name_in.clear(); self.save_data()

    def buy_store_item(self, item):
        d = item.data(Qt.UserRole)
        if self.total_points >= d["pts"]:
            self.total_points -= d["pts"]; self.time_bank[d["name"]] += d["min"] * 60
            self.add_log("支出", f"购买时长: {d['name']}", -d['pts']); self.update_all_ui(); self.save_data()

    def buy_reward_direct(self, item):
        d = item.data(Qt.UserRole)
        if self.total_points >= d["pts"]:
            self.total_points -= d["pts"]; self.history_list.addItem(f"领用: {d['name']}")
            self.add_log("支出", f"领用奖励: {d['name']}", -d['pts']); self.update_all_ui(); self.save_data()

    # --- 辅助逻辑 ---
    def refresh_stats(self):
        self.log_tasks.clear(); self.log_points.clear()
        ty, tm = int(self.year_combo.currentText()), self.month_combo.currentData()
        gain = 0
        for log in reversed(self.history_logs):
            if log["time"].year == ty and log["time"].month == tm:
                t_str = log["time"].strftime("%m-%d %H:%M")
                if log["type"] == "任务":
                    gain += log["points"]
                    self.log_tasks.addItem(f"[{t_str}] {log['name']} | 用时: {log['duration']}min | 收益: +{log['points']}")
                sign = "+" if log["points"] > 0 else ""
                self.log_points.addItem(f"[{t_str}] {log['name']} : {sign}{log['points']}")
        self.lbl_month_total.setText(f"📅 {ty}年{tm}月 累计收益: {gain} 分")

    def show_del_menu(self, widget, pos):
        menu = QMenu(); del_act = menu.addAction("🗑️ 删除")
        if menu.exec(widget.mapToGlobal(pos)) == del_act: 
            widget.takeItem(widget.currentRow()); self.save_data()

    def add_store_item(self):
        n, p, m = self.s_name_in.text(), int(self.s_pts_in.text() or 0), int(self.s_min_in.text() or 0)
        item = QListWidgetItem(f"{n} | {p}分 | +{m}min"); item.setData(Qt.UserRole, {"name": n, "pts": p, "min": m})
        self.store_list.addItem(item)
        if n not in self.time_bank: self.time_bank[n] = 0; self.consume_list.addItem(n); self.save_data()

    def start_consume_logic(self, item):
        if self.time_bank.get(item.text(), 0) > 0: self.active_consume_type = item.text(); self.store_timer.start(1000)

    def update_store_timer(self):
        cat = self.active_consume_type
        if self.time_bank[cat] > 0:
            self.time_bank[cat] -= 1; m, s = divmod(self.time_bank[cat], 60)
            self.label_s_status.setText(f"消费【{cat}】中: 剩 {m:02d}:{s:02d}"); self.update_all_ui()
        else: self.total_points -= 1; self.update_all_ui(); self.label_s_status.setText("⚠️ 余额空！倒扣积分中！")
        if self.time_bank[cat] % 60 == 0: self.save_data() # 每分钟存一次档

    def stop_consuming(self): self.store_timer.stop(); self.active_consume_type = None; self.label_s_status.setText("状态: 闲置"); self.save_data()

    def add_reward_item(self):
        n, p = self.r_name_in.text(), int(self.r_pts_in.text() or 0)
        item = QListWidgetItem(f"🎁 {n} | {p}分"); item.setData(Qt.UserRole, {"name": n, "pts": p})
        self.reward_list.addItem(item); self.save_data()

    def toggle_task_timer(self):
        if self.main_timer.isActive(): self.main_timer.stop()
        else: self.main_timer.start(1000)

    def on_timer_tick(self):
        it = self.task_list.currentItem()
        if it:
            tk = it.data(Qt.UserRole)
            if not tk.is_completed and tk.task_type != "签到":
                tk.elapsed_seconds += 1; m, s = divmod(tk.elapsed_seconds, 60)
                self.label_task_time.setText(f"用时: {m:02d}:{s:02d}")

    def manual_record(self):
        it = self.task_list.currentItem()
        if it: m, ok = QInputDialog.getInt(self, "补录", "分钟:", 20, 1, 600); it.data(Qt.UserRole).elapsed_seconds = m * 60; self.save_data()

    def update_all_ui(self):
        self.points_label.setText(f"💰 当前总积分: {self.total_points}")
        txt = [f"{k}: {v//60}min" for k, v in self.time_bank.items() if v > 0]
        self.bank_display.setText("银行余额: " + (" | ".join(txt) if txt else "空"))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LearningApp(); window.show()
    sys.exit(app.exec())