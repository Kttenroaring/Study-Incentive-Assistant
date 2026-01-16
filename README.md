学习积分助手 (Study Incentive Assistant) 🚀
简体中文 | English

🇨🇳 项目简介
这是一个基于 Python 开发的全平台桌面与移动实用程序。它通过“积分经济学”逻辑，将学习任务转化为可量化的收益，并引入金融复利概念，旨在彻底解决学习拖延症。

📸 界面预览 (Preview)
✨ 核心功能
四分区任务架构：精准分类“一次性任务、常规任务、定时签到、已完成”，任务流转逻辑清晰。

金融激励系统：

0.1% 复利结息：账户余额每日自动结算利息，鼓励长线积分储蓄。

时长商店：支持积分购买娱乐时长，内置消费倒计时辅助自我管理。

全平台支持：

桌面端 (PySide6)：功能全开，支持右键管理、月度收益详细统计。

手机端 (Kivy/Android)：支持随时随地打卡，数据同步便捷（注：需手动同步数据文件）。

可视化统计：支持按月份精准查询任务净收益，红色高亮支出明细。

🛠️ 技术栈
GUI 框架:

Desktop: PySide6 (Qt 6)

Mobile: Kivy (Cross-platform UI)

数据持久化: Pickle (二进制序列化，确保跨平台数据结构一致)

核心算法: 动态复利结算、任务分拣模糊匹配算法。

🇺🇸 Introduction
A cross-platform productivity ecosystem built with Python, designed to gamify learning through a sophisticated "Point Economics" and "Compound Interest" system.

✨ Key Features
Four-Quadrant Management: Categorized sections for One-time, Routine, Sign-in, and Completed tasks.

Economic Incentives:

0.1% Compound Interest: Daily interest credited automatically to reward long-term point saving.

Time Store: Purchase entertainment duration with points, featuring an integrated countdown timer.

Multi-Platform Support:

Desktop (PySide6): Full-featured version with right-click menus and detailed statistics.

Mobile (Kivy/Android): Optimized for on-the-go check-ins and task tracking.

Advanced Analytics: Monthly gain tracking that isolates "Task Profit" from other expenditures.

🛠️ Tech Stack
Frameworks:

Desktop: PySide6 (Qt 6)

Mobile: Kivy

Persistence: Pickle (Binary serialization for cross-platform consistency)

Algorithms: Dynamic interest calculation & fuzzy logic for task sorting.

🚀 如何运行 (How to Run)
💻 桌面端 (Desktop)
安装依赖: pip install PySide6

运行程序: python main.py

📱 手机端 (Mobile)
确保安装了 Kivy 环境。

编译为 APK (使用 Buildozer) 或在 Kivy Launcher 中运行。

将 learning_data.dat 放入对应目录即可同步数据。

💡 提示 / Tip
程序会自动在目录下生成 learning_data.dat 用于保存数据。桌面端和手机端共用同一种数据格式。 The app uses learning_data.dat for storage. The data format is consistent across both Desktop and Mobile versions.


💡 提示 / Tip
程序会自动在目录下生成 learning_data.dat 用于保存数据。桌面端和手机端共用同一种数据格式。 The app uses learning_data.dat for storage. The data format is consistent across both Desktop and Mobile versions.
