# -*- coding: utf-8 -*-
import sys
import pickle
import os
import requests
import json
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
        self.setWindowTitle("学习积分助手 v1.6.9 - 稳定修复版")
        
        self.data_file = "learning_data.dat"
        self.total_points = 0
        self.time_bank = {} 
        self.history_logs = []
        self.last_interest_date = ""
        self.active_consume_type = None

        self.init_ui()
        self.load_data() 

        self.main_timer = QTimer()
        self.main_timer.timeout.connect(self.on_timer_tick)
        self.store_timer = QTimer()
        self.store_timer.timeout.connect(self.update_store_timer)

    def init_ui(self):
        self.setGeometry(100, 100, 1100, 800)
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)

        self.points_label = QLabel(f"💰 当前总积分: {self.total_points}")
        self.points_label.setStyleSheet("font-size: 24px; color: #E67E22; font-weight: bold; padding: 10px;")
        self.main_layout.addWidget(self.points_label)

        self.tab_widget = QTabWidget()
        self.main_layout.addWidget(self.tab_widget)

        self.create_task_tab()
        self.create_store_tab()
        self.create_reward_tab() # ✨ 补回实物奖励页签
        self.create_stat_tab()

    def create_task_tab(self):
        tab = QWidget(); layout = QVBoxLayout(tab)
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
        self.task_list = QListWidget()
        self.task_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.task_list.customContextMenuRequested.connect(self.show_task_menu)
        layout.addWidget(self.task_list)
        
        ctrl = QHBoxLayout()
        self.label_task_time = QLabel("计时: 00:00")
        btn_start = QPushButton("开始/暂停"); btn_start.clicked.connect(self.toggle_task_timer)
        btn_finish = QPushButton("结算任务"); btn_finish.clicked.connect(self.finish_task)
        ctrl.addWidget(self.label_task_time); ctrl.addWidget(btn_start); ctrl.addWidget(btn_finish)
        layout.addLayout(ctrl); self.tab_widget.addTab(tab, "学习任务")

    def create_store_tab(self):
        tab = QWidget(); layout = QVBoxLayout(tab)
        add_box = QHBoxLayout()
        self.s_name_in = QLineEdit(); self.s_pts_in = QLineEdit(); self.s_min_in = QLineEdit()
        self.s_name_in.setPlaceholderText("商品名"); self.s_pts_in.setPlaceholderText("积分"); self.s_min_in.setPlaceholderText("分钟")
        btn_s_add = QPushButton("上架商品"); btn_s_add.clicked.connect(self.add_store_item)
        add_box.addWidget(self.s_name_in); add_box.addWidget(self.s_pts_in); add_box.addWidget(self.s_min_in); add_box.addWidget(btn_s_add)
        layout.addLayout(add_box)
        
        self.store_list = QListWidget()
        self.store_list.itemClicked.connect(self.buy_store_item)
        layout.addWidget(QLabel("🛒 点击购买:"))
        layout.addWidget(self.store_list)
        
        self.bank_display = QLabel("银行余额: 空")
        self.bank_display.setStyleSheet("background:#f0f0f0; padding:10px; font-weight:bold;")
        layout.addWidget(self.bank_display)
        
        self.consume_list = QListWidget()
        self.consume_list.itemClicked.connect(self.start_consume_logic)
        self.consume_list.setContextMenuPolicy(Qt.CustomContextMenu) 
        self.consume_list.customContextMenuRequested.connect(self.show_refund_menu)
        layout.addWidget(QLabel("🚀 点击消费 (右键退货):"))
        layout.addWidget(self.consume_list)
        
        self.label_s_status = QLabel("状态: 闲置")
        btn_stop = QPushButton("停止消费"); btn_stop.clicked.connect(self.stop_consuming)
        layout.addWidget(self.label_s_status); layout.addWidget(btn_stop)
        self.tab_widget.addTab(tab, "时长商店")

    def create_reward_tab(self):
        """✨ 补回遗失的实物奖励页签"""
        tab = QWidget(); layout = QVBoxLayout(tab)
        h_box = QHBoxLayout()
        self.r_name_in = QLineEdit(); self.r_name_in.setPlaceholderText("实物奖品名称")
        self.r_pts_in = QLineEdit(); self.r_pts_in.setPlaceholderText("扣除积分")
        btn_r_add = QPushButton("上架"); btn_r_add.clicked.connect(self.add_reward_item)
        h_box.addWidget(self.r_name_in); h_box.addWidget(self.r_pts_in); h_box.addWidget(btn_r_add)
        layout.addLayout(h_box)

        self.reward_list = QListWidget()
        self.reward_list.itemClicked.connect(self.redeem_reward)
        layout.addWidget(QLabel("🎁 点击奖品直接领取:"))
        layout.addWidget(self.reward_list)
        self.tab_widget.addTab(tab, "实物奖励")

    def show_task_menu(self, pos):
        item = self.task_list.itemAt(pos)
        if not item: return
        menu = QMenu()
        del_act = menu.addAction("🗑️ 删除任务")
        # 修正：使用 exec() 接收菜单动作
        action = menu.exec(self.task_list.mapToGlobal(pos))
        if action == del_act:
            self.task_list.takeItem(self.task_list.row(item))
            self.save_data()

    def show_refund_menu(self, pos):
        item = self.consume_list.itemAt(pos)
        if not item: return
        menu = QMenu()
        refund_act = menu.addAction("💰 退货 (返还积分并清空该项)")
        action = menu.exec(self.consume_list.mapToGlobal(pos))
        
        if action == refund_act:
            name = item.text()
            refund_pts = 0
            for log in reversed(self.history_logs):
                if log["type"] == "支出" and name in log["name"]:
                    refund_pts = abs(log["points"])
                    break
            
            if refund_pts > 0:
                self.total_points += refund_pts
                if name in self.time_bank: del self.time_bank[name]
                self.add_log("退货", f"退还: {name}", refund_pts)
                self.sync_consume_list(); self.update_all_ui(); self.save_data()
                QMessageBox.information(self, "成功", f"已退还 {refund_pts} 积分。")

    def create_stat_tab(self):
        tab = QWidget(); layout = QVBoxLayout(tab)
        self.year_combo = QComboBox(); self.year_combo.addItem("2026")
        self.month_combo = QComboBox()
        for i in range(1, 13): self.month_combo.addItem(f"{i}月", i)
        self.month_combo.setCurrentIndex(datetime.now().month - 1)
        btn_refresh = QPushButton("🔍 刷新统计"); btn_refresh.clicked.connect(self.refresh_stats)
        
        layout.addWidget(self.year_combo); layout.addWidget(self.month_combo); layout.addWidget(btn_refresh)
        self.lbl_month_total = QLabel("本月收益: 0 分")
        self.lbl_month_total.setStyleSheet("font-size: 18px; color: #27ae60; font-weight:bold;")
        self.log_points = QListWidget()
        layout.addWidget(self.lbl_month_total); layout.addWidget(self.log_points)
        self.tab_widget.addTab(tab, "统计成果")

    def load_data(self):
        """数据兼容性修复逻辑"""
        if not os.path.exists(self.data_file): return
        try:
            with open(self.data_file, "rb") as f:
                data = pickle.load(f)
                self.total_points = data.get("points", 0)
                self.time_bank = data.get("bank", {})
                self.history_logs = data.get("logs", [])
                self.last_interest_date = data.get("last_interest_date", "")
                
                self.task_list.clear()
                for task in data.get("tasks", []):
                    # 补全缺失属性 
                    if not hasattr(task, 'current_daily'): task.current_daily = 0
                    if not hasattr(task, 'max_daily'): task.max_daily = 1
                    if not hasattr(task, 'is_completed'): task.is_completed = False
                    
                    item = QListWidgetItem()
                    item.setData(Qt.UserRole, task)
                    self.update_task_display(item, task)
                    self.task_list.addItem(item)
                
                self.calculate_interest()
                self.sync_consume_list(); self.update_all_ui(); self.refresh_stats()
        except Exception as e:
            print(f"数据加载失败: {e}")

    def finish_task(self): 
        item = self.task_list.currentItem()
        if not item: return
        task = item.data(Qt.UserRole)
        
        today = datetime.now().strftime("%Y-%m-%d")
        if getattr(task, 'last_date', "") != today:
            task.current_daily = 0
            task.last_date = today
            if task.task_type != "一次性": task.is_completed = False

        if task.is_completed: 
            QMessageBox.warning(self, "提醒", "该任务今日已达上限！")
            return
        
        self.main_timer.stop()
        self.total_points += task.base_points
        self.add_log("任务", task.name, task.base_points)
        
        task.current_daily = getattr(task, 'current_daily', 0) + 1
        if task.task_type == "一次性" or task.current_daily >= getattr(task, 'max_daily', 1):
            task.is_completed = True
            
        self.update_task_display(item, task)
        self.update_all_ui(); self.save_data()

    def calculate_interest(self):
        """
        ✨ 简体中文优化版结息逻辑
        功能：支持极小金额结息，保留4位小数，确保增长可见。
        """
        # 获取当前日期
        today_dt = datetime.now().date()
        today_str = today_dt.strftime("%Y-%m-%d")
        
        # 如果是第一次运行，记录今天日期并退出
        if not self.last_interest_date: 
            self.last_interest_date = today_str
            return
            
        try:
            # 计算距离上次结息过了几天
            last_dt = datetime.strptime(self.last_interest_date, "%Y-%m-%d").date()
            days = (today_dt - last_dt).days
            
            # 如果日期已经跳到第二天或更久
            if days > 0:
                # 计算利息：当前总分 * 0.1% (0.001) * 天数
                earned = self.total_points * 0.001 * days
                
                # 只要利息大于 0 就发放并记录
                if earned > 0:
                    self.total_points += earned
                    # 在统计记录中保留4位小数
                    self.add_log("利息", f"{days}天自动结息 (日率0.1%)", round(earned, 4))
                
                # 更新结息日期为今天，防止重复计算
                self.last_interest_date = today_str
                # 保存数据，确保利息不会因为意外关闭而丢失
                self.save_data()
                # 刷新主界面显示的积分
                self.update_all_ui() 
                
        except Exception as e:
            print(f"结息过程出错: {e}")

    def add_log(self, l_type, name, points):
        self.history_logs.append({"time": datetime.now(), "type": l_type, "name": name, "points": points})
        self.refresh_stats()

    def update_task_display(self, item, task):
        limit = f"({getattr(task, 'current_daily', 0)}/{getattr(task, 'max_daily', 1)})" if task.task_type != "一次性" else ""
        item.setText(f"{'✅' if task.is_completed else '🕒'} [{task.task_type}] {task.name} {limit}")
        item.setForeground(Qt.gray if task.is_completed else Qt.black)

    def add_task(self):
        n = self.t_name_in.text(); m = int(self.t_min_in.text() or 0); p = int(self.t_pts_in.text() or 0)
        limit = int(self.t_limit_in.text() or 1) 
        if not n: return
        t_type = ["一次性", "常规任务", "定时签到"][self.t_type_group.checkedId()]
        task = Task(n, t_type, m, p, max_daily=limit)
        item = QListWidgetItem(); item.setData(Qt.UserRole, task)
        self.update_task_display(item, task); self.task_list.addItem(item)
        self.save_data(); self.t_name_in.clear()

    def add_store_item(self): 
        n = self.s_name_in.text(); p = int(self.s_pts_in.text() or 0); m = int(self.s_min_in.text() or 0)
        if not n: return
        item = QListWidgetItem(f"🎁 {n} | {p}分 | {m}分钟")
        item.setData(Qt.UserRole, {"name": n, "pts": p, "min": m})
        self.store_list.addItem(item)
        if n not in self.time_bank: self.time_bank[n] = 0
        self.sync_consume_list(); self.save_data(); self.s_name_in.clear()

    def buy_store_item(self, item):
        d = item.data(Qt.UserRole)
        if self.total_points >= d["pts"]:
            self.total_points -= d["pts"]
            self.time_bank[d["name"]] = self.time_bank.get(d["name"], 0) + d["min"] * 60
            self.add_log("支出", f"购买: {d['name']}", -d['pts'])
            self.sync_consume_list(); self.update_all_ui(); self.save_data()
        else:
            QMessageBox.warning(self, "积分不足", "积分不够哦！")

    def add_reward_item(self):
        n = self.r_name_in.text(); p = int(self.r_pts_in.text() or 0)
        if not n: return
        item = QListWidgetItem(f"🏆 {n} | 需 {p} 分")
        item.setData(Qt.UserRole, {"name": n, "pts": p})
        self.reward_list.addItem(item); self.r_name_in.clear(); self.save_data()

    def redeem_reward(self, item):
        d = item.data(Qt.UserRole)
        if self.total_points >= d["pts"]:
            self.total_points -= d["pts"]
            self.add_log("实物", f"领取: {d['name']}", -d['pts'])
            self.update_all_ui(); self.save_data()
            QMessageBox.information(self, "成功", f"领取【{d['name']}】成功！")
        else:
            QMessageBox.warning(self, "积分不足", "再努力学习一下吧！")

    def start_consume_logic(self, item):
        cat = item.text()
        if self.time_bank.get(cat, 0) > 0: # 修正：已移除干扰文本 [cite: 128]
            self.active_consume_type = cat
            self.store_timer.start(1000)
            self.label_s_status.setText(f"🔥 正在消费: {cat}")
        else:
            QMessageBox.warning(self, "余额不足", f"【{cat}】没有剩余时间了！")

    def update_store_timer(self):
        cat = self.active_consume_type
        if cat and self.time_bank.get(cat, 0) > 0:
            self.time_bank[cat] -= 1
            m, s = divmod(self.time_bank[cat], 60)
            self.label_s_status.setText(f"🔥 {cat} 剩余: {m:02d}:{s:02d}")
            self.update_all_ui()
        else:
            self.stop_consuming()

    def stop_consuming(self):
        self.store_timer.stop(); self.active_consume_type = None; self.label_s_status.setText("状态: 闲置")
        self.update_all_ui(); self.save_data()

    def refresh_stats(self):
        self.log_points.clear()
        selected_month = self.month_combo.currentData()
        gain = 0
        for log in reversed(self.history_logs):
            if log["time"].month == selected_month:
                pts = log["points"]
                it = QListWidgetItem(f"[{log['time'].strftime('%m-%d %H:%M')}] {log['name']}: {pts}")
                if pts < 0: it.setForeground(Qt.red)
                self.log_points.addItem(it)
                if log['type'] == "任务": gain += pts
        self.lbl_month_total.setText(f"本月收益: {gain} 分")

    def save_data(self):
        try: # 修正：已移除干扰文本 [cite: 144]
            tasks = [self.task_list.item(i).data(Qt.UserRole) for i in range(self.task_list.count())]
            data = {"points": self.total_points, "bank": self.time_bank, "logs": self.history_logs, "tasks": tasks, "last_interest_date": self.last_interest_date}
            with open(self.data_file, "wb") as f: pickle.dump(data, f)
        except: pass

    def sync_consume_list(self):
        self.consume_list.clear()
        for k in self.time_bank.keys(): self.consume_list.addItem(k)

    def update_all_ui(self):
        self.points_label.setText(f"💰 当前总积分: {round(self.total_points, 2)}")
        txt = [f"{k}: {v//60}分" for k, v in self.time_bank.items() if v > 0]
        self.bank_display.setText("余额: " + (" | ".join(txt) if txt else "空"))

    def on_timer_tick(self):
        it = self.task_list.currentItem()
        if it:
            tk = it.data(Qt.UserRole)
            if not tk.is_completed:
                tk.elapsed_seconds += 1
                m, s = divmod(tk.elapsed_seconds, 60)
                self.label_task_time.setText(f"计时: {m:02d}:{s:02d}")

    def toggle_task_timer(self):
        if self.main_timer.isActive(): self.main_timer.stop()
        else: self.main_timer.start(1000)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = LearningApp(); window.show()
    sys.exit(app.exec())
