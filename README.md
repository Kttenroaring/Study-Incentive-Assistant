# Study Incentive Assistant 🚀

一个基于积分激励系统的跨平台生产力工具，通过游戏化机制提升学习效率

[简体中文](#简体中文) | [English](#english)

---

## 🇨🇳 简体中文

### 📋 项目简介
这是一个基于 Python 开发的跨平台（桌面端 & 移动端）生产力工具，通过“积分经济学”和金融复利概念，将学习任务转化为量化收益，旨在有效激励学习。

### 📸 界面预览  (Preview)
<img width="1715" height="1313" alt="image" src="https://github.com/user-attachments/assets/18620dcd-db32-466c-a996-9ec510ec6a30" />
<img width="1734" height="1322" alt="image" src="https://github.com/user-attachments/assets/09fa159c-67e4-484c-afcf-0c171d23e290" />


### ✨ 核心特性

#### 📊 四分区任务管理
- **一次性任务**：短期目标与临时任务
- **常规任务**：每日/周期性重复任务
- **定时签到**：时间点打卡任务
- **已完成**：历史任务归档

#### 💰 金融激励系统
- **0.1% 复利结息**：账户余额每日自动结算利息，鼓励长期储蓄
- **时长商店**：使用积分购买娱乐时长，内置倒计时功能
- **积分消费**：支持灵活积分兑换与消费记录

#### 📱 多端联动
- **移动端支持**：基于 Kivy 开发，支持随时随地打卡
- **数据同步**：移动端与桌面端数据格式完全兼容
- **跨平台体验**：无缝切换设备，保持学习连续性

#### 📈 可视化统计
- **月度报表**：按月份查询学习成果与积分变化
- **收支明细**：红色高亮支出记录，收益一目了然
- **趋势分析**：直观展示学习习惯与积分积累趋势

### 🛠️ 技术栈
- **开发语言**：Python 3.x
- **桌面框架**：PySide6 (Qt 6)
- **移动框架**：Kivy (跨平台)
- **数据持久化**：Pickle 对象序列化
- **版本控制**：Git

### 🚀 快速开始

#### 桌面端运行
```bash
# 1. 克隆项目
git clone <repository-url>
cd Study-Incentive-Assistant

# 2. 安装依赖
pip install PySide6

# 3. 运行程序
python main.py
```

#### 移动端使用
1. 将桌面端生成的 `learning_data.dat` 文件复制到移动端对应目录
2. 安装移动端应用（Kivy 环境）
3. 数据自动同步，随时随地继续学习


## 🇺🇸 English

### 📋 Introduction
A professional cross-platform productivity ecosystem built with Python, designed to boost learning efficiency through a gamified "Point Economics" and "Compound Interest" system.

### ✨ Key Features

#### 📊 4-Quadrant Task Management
- **One-time Tasks**: Short-term goals and ad-hoc assignments
- **Routine Tasks**: Daily/periodic recurring tasks
- **Timed Check-ins**: Scheduled checkpoints
- **Completed**: Historical task archive

#### 💰 Economic Incentives
- **0.1% Compound Interest**: Daily automatic interest calculation to encourage saving
- **Time Store**: Purchase "Entertainment Time" with points, featuring integrated timer
- **Point Consumption**: Flexible point exchange with detailed records

#### 📱 Multi-Device Support
- **Mobile Version**: Kivy-based application for on-the-go productivity
- **Data Sync**: Seamless compatibility between desktop and mobile data formats
- **Cross-Platform**: Continuity across all your devices

#### 📈 Visual Statistics
- **Monthly Reports**: Track learning progress and point fluctuations
- **Income/Expense Details**: Clear visualization with highlighted expenditures
- **Trend Analysis**: Insights into study habits and point accumulation trends

### 🛠️ Tech Stack
- **Language**: Python 3.x
- **GUI (Desktop)**: PySide6 (Qt 6)
- **GUI (Mobile)**: Kivy
- **Persistence**: Pickle Serialization
- **Version Control**: Git

### 🚀 Quick Start

#### Desktop Installation
```bash
# 1. Clone repository
git clone <repository-url>
cd Study-Incentive-Assistant

# 2. Install dependencies
pip install PySide6

# 3. Run application
python main.py
```

#### Mobile Setup
1. Copy `learning_data.dat` from desktop to mobile directory
2. Install mobile app (Kivy environment)
3. Data automatically syncs - continue learning anywhere

---

## 📄 License
MIT License - see LICENSE file for details

## ⭐ Support
If you find this project helpful, please consider giving it a star on GitHub!

---

*This README is optimized for better readability and includes clear section separations. The bilingual format maintains consistency while providing accessibility for both Chinese and English speakers.*
