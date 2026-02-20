import sys
import os
from PyQt6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                             QHBoxLayout, QPushButton, QLabel, QLineEdit, 
                             QTextEdit, QListWidget, QFileDialog, QMessageBox,
                             QSplitter, QGroupBox, QListWidgetItem)
from PyQt6.QtCore import Qt, QThread, pyqtSignal, QSettings

import search_engine
from document_parser import parse_document
from search_engine import perform_search
from deepseek_api import analyze_with_deepseek

class WorkerThread(QThread):
    finished = pyqtSignal(object)
    error = pyqtSignal(str)
    
    def __init__(self, func, *args, **kwargs):
        super().__init__()
        self.func = func
        self.args = args
        self.kwargs = kwargs
        
    def run(self):
        try:
            result = self.func(*self.args, **self.kwargs)
            self.finished.emit(result)
        except Exception as e:
            self.error.emit(str(e))


class LogicEngine:
    def __init__(self):
        self.documents_data = []

    def clear_documents(self):
        self.documents_data = []
        
    def add_document(self, filepath):
        data = parse_document(filepath)
        self.documents_data.extend(data)
        return len(data)
        
    def add_documents(self, filepaths):
        total_len = 0
        for fp in filepaths:
            total_len += self.add_document(fp)
        return total_len
        
    def search(self, query):
        if not self.documents_data:
            return None, "错误：没有任何文档数据，请先添加文档。"
        
        matched_q, matches = perform_search(query, self.documents_data)
        if matched_q and matches:
            return matched_q, matches
        else:
            return None, "未找到相关的关键词信息。"
            
    def reverse_search(self, keyword):
        if not self.documents_data:
            return None, "错误：没有任何文档数据，请先添加文档。"
        
        matches = search_engine.reverse_search(keyword, self.documents_data)
        if matches:
            return "ok", matches
        else:
            return None, "未找到相关的分类信息。"

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.engine = LogicEngine()
        self.settings = QSettings('KeywordApp', 'KeywordSearchTool')
        self.initUI()
        self.startup_load()
        
    def initUI(self):
        self.setWindowTitle("关键词分析与搜索工具 v1.0")
        self.resize(1100, 750)
        
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        
        # Main vertical layout
        vbox_main = QVBoxLayout(main_widget)
        
        # Top Settings (API Key)
        hbox_top = QHBoxLayout()
        hbox_top.addWidget(QLabel("DeepSeek API Key:"))
        self.api_key_input = QLineEdit()
        self.api_key_input.setText(self.settings.value('api_key', ''))
        self.api_key_input.setPlaceholderText("填入您的 DeepSeek API Key (用以调用大模型)")
        self.api_key_input.setEchoMode(QLineEdit.EchoMode.PasswordEchoOnEdit)
        # 实时保存 API Key
        self.api_key_input.textChanged.connect(lambda t: self.settings.setValue('api_key', t))
        hbox_top.addWidget(self.api_key_input)
        vbox_main.addLayout(hbox_top)
        
        # Splitter for left and right areas
        splitter = QSplitter(Qt.Orientation.Horizontal)
        vbox_main.addWidget(splitter)
        
        # --- Left Panel ---
        left_widget = QWidget()
        vbox_left = QVBoxLayout(left_widget)
        vbox_left.setContentsMargins(0, 0, 0, 0)
        
        group_doc = QGroupBox("1. 文档管理")
        vbox_doc = QVBoxLayout(group_doc)
        
        hbox_doc_btns = QHBoxLayout()
        btn_add_file = QPushButton("添加")
        btn_add_file.clicked.connect(self.on_add_file)
        btn_remove_file = QPushButton("移除")
        btn_remove_file.clicked.connect(self.on_remove_file)
        hbox_doc_btns.addWidget(btn_add_file)
        hbox_doc_btns.addWidget(btn_remove_file)
        
        self.list_files = QListWidget()
        vbox_doc.addLayout(hbox_doc_btns)
        vbox_doc.addWidget(self.list_files)
        vbox_left.addWidget(group_doc)
        
        group_search = QGroupBox("2. 检索区")
        vbox_search = QVBoxLayout(group_search)
        
        self.input_ipc = QLineEdit()
        self.input_ipc.setPlaceholderText("输入分类号检索，例如 G06F3/01")
        self.input_ipc.returnPressed.connect(self.on_search)
        btn_search = QPushButton("正向检索 (分类号 -> 关键词)")
        btn_search.clicked.connect(self.on_search)
        
        self.input_kw = QLineEdit()
        self.input_kw.setPlaceholderText("输入关键词反查，例如 机器学习")
        self.input_kw.returnPressed.connect(self.on_reverse_search)
        btn_reverse_search = QPushButton("反向检索 (关键词 -> 分类号)")
        btn_reverse_search.clicked.connect(self.on_reverse_search)
        
        vbox_search.addWidget(QLabel("目标分类号:"))
        vbox_search.addWidget(self.input_ipc)
        vbox_search.addWidget(btn_search)
        
        vbox_search.addSpacing(10)
        vbox_search.addWidget(QLabel("目标关键词:"))
        vbox_search.addWidget(self.input_kw)
        vbox_search.addWidget(btn_reverse_search)
        
        vbox_left.addWidget(group_search)
        
        # --- Right Panel ---
        # 改为垂直 Splitter 以便灵活拉伸上下部分
        right_splitter = QSplitter(Qt.Orientation.Vertical)
        
        group_keywords = QGroupBox("3. 提取的关键词结果")
        vbox_keywords = QVBoxLayout(group_keywords)
        self.text_keywords = QTextEdit()
        self.text_keywords.setReadOnly(True)
        vbox_keywords.addWidget(self.text_keywords)
        right_splitter.addWidget(group_keywords)
        
        group_analyze = QGroupBox("4. DeepSeek 智能分析")
        vbox_analyze = QVBoxLayout(group_analyze)
        
        # 将输入框也加入一个小的 Splitter 保证灵活性，或直接依赖外层
        self.input_text = QTextEdit()
        self.input_text.setPlaceholderText("输入待分析的一段文字...")
        # 取消最大高度限制，使得它也能被自由拉伸扩容
        self.input_text.setMinimumHeight(60)
        
        btn_analyze = QPushButton("开始 AI 分析")
        btn_analyze.clicked.connect(self.on_analyze)
        
        self.text_result = QTextEdit()
        self.text_result.setReadOnly(True)
        self.text_result.setPlaceholderText("分析结果将显示在这里...")
        
        # Layout inside analyze group
        inner_analyze_splitter = QSplitter(Qt.Orientation.Vertical)
        
        widget_analyze_top = QWidget()
        vbox_analyze_top = QVBoxLayout(widget_analyze_top)
        vbox_analyze_top.setContentsMargins(0, 0, 0, 0)
        vbox_analyze_top.addWidget(QLabel("待分析文字:"))
        vbox_analyze_top.addWidget(self.input_text)
        vbox_analyze_top.addWidget(btn_analyze)
        
        widget_analyze_bottom = QWidget()
        vbox_analyze_bottom = QVBoxLayout(widget_analyze_bottom)
        vbox_analyze_bottom.setContentsMargins(0, 0, 0, 0)
        vbox_analyze_bottom.addWidget(QLabel("分析结果:"))
        vbox_analyze_bottom.addWidget(self.text_result)
        
        inner_analyze_splitter.addWidget(widget_analyze_top)
        inner_analyze_splitter.addWidget(widget_analyze_bottom)
        inner_analyze_splitter.setSizes([150, 300])
        
        vbox_analyze.addWidget(inner_analyze_splitter)
        right_splitter.addWidget(group_analyze)
        
        # 初始Right Splitter占比 (提取结果占多点)
        right_splitter.setSizes([400, 450])
        
        splitter.addWidget(left_widget)
        splitter.addWidget(right_splitter)
        
        # 左侧变窄，右侧放大
        splitter.setSizes([220, 880])
        
    def set_gui_enabled(self, enabled):
        """Disable/Enable interactions during long running tasks"""
        self.centralWidget().setEnabled(enabled)

    def startup_load(self):
        saved_docs = self.settings.value('docs', [])
        if isinstance(saved_docs, str): saved_docs = [saved_docs]
        elif not isinstance(saved_docs, list): saved_docs = []
        
        valid_docs = [d for d in saved_docs if os.path.exists(d)]
        
        for d in valid_docs:
            item = QListWidgetItem(os.path.basename(d))
            item.setData(Qt.ItemDataRole.UserRole, d)
            self.list_files.addItem(item)
            
        if valid_docs:
            self.set_gui_enabled(False)
            self.text_keywords.setPlainText("正在为您恢复上次加载的文档知识库，请稍候...")
            self.worker = WorkerThread(self.engine.add_documents, valid_docs)
            self.worker.finished.connect(self.on_startup_finished)
            self.worker.error.connect(self.on_error)
            self.worker.start()

    def on_startup_finished(self, cnt):
        self.set_gui_enabled(True)
        self.text_keywords.setPlainText(f"文档库加载完毕，共抽取就绪 {cnt} 条关联数据。现在可以开始搜索了！")

    def _save_docs_to_settings(self):
        docs = []
        for i in range(self.list_files.count()):
            docs.append(self.list_files.item(i).data(Qt.ItemDataRole.UserRole))
        self.settings.setValue('docs', docs)

    def _reload_all_docs(self):
        self.engine.clear_documents()
        docs = self.settings.value('docs', [])
        if not isinstance(docs, list): docs = []
        
        if docs:
            self.set_gui_enabled(False)
            self.text_keywords.setPlainText("正在重新同步您的文档知识库...")
            self.worker = WorkerThread(self.engine.add_documents, docs)
            self.worker.finished.connect(self.on_startup_finished)
            self.worker.error.connect(self.on_error)
            self.worker.start()
        else:
            self.text_keywords.setPlainText("文档列表已被清空。")

    def on_add_file(self):
        filepath, _ = QFileDialog.getOpenFileName(self, "选择文档", "", "PDF Files (*.pdf);;All Files (*)")
        if filepath:
            for i in range(self.list_files.count()):
                if self.list_files.item(i).data(Qt.ItemDataRole.UserRole) == filepath:
                    QMessageBox.warning(self, "提示", "该文档已经在列表中！")
                    return
                    
            self.set_gui_enabled(False)
            item = QListWidgetItem(os.path.basename(filepath))
            item.setData(Qt.ItemDataRole.UserRole, filepath)
            self.list_files.addItem(item)
            
            self._save_docs_to_settings()
            
            self.worker = WorkerThread(self.engine.add_document, filepath)
            self.worker.finished.connect(self.on_add_file_finished)
            self.worker.error.connect(self.on_error)
            self.worker.start()
            
    def on_remove_file(self):
        selected = self.list_files.selectedItems()
        if not selected:
            QMessageBox.warning(self, "提示", "请先在列表中选中要移除的文档。")
            return
            
        for item in selected:
            self.list_files.takeItem(self.list_files.row(item))
            
        self._save_docs_to_settings()
        self._reload_all_docs()
            
    def on_add_file_finished(self, count):
        self.set_gui_enabled(True)
        QMessageBox.information(self, "成功", f"成功追加解析文档，提取了 {count} 条数据。")
        self.text_keywords.setPlainText(f"追加文档成功：已加入 {count} 条数据记录。")
        
    def on_search(self):
        query = self.input_ipc.text().strip()
        if not query:
            QMessageBox.warning(self, "错误", "请输入分类号")
            return
            
        matched_q, matches = self.engine.search(query)
        if matched_q and matches:
            display_text = f"【匹配到分类号】: {matched_q}\n\n"
            raw_keywords_list = []
            
            for m in matches if isinstance(matches, list) else []:
                src = m.get('source', '')
                page = m.get('page', '')
                ctx = m.get('context_text', '').replace('\n', ' ')
                kw = m.get('keywords_text', '').replace('\n', ' ')
                
                title_str = ""
                if src:
                    title_str += f"《{src.replace('.pdf', '')}》"
                if page:
                    title_str += f"-第{page}页"
                    
                display_text += f"{title_str}-{ctx}\n"
                display_text += f"匹配关键词: {kw}\n"
                display_text += "-" * 40 + "\n"
                
                raw_keywords_list.append(kw)
                
            self.text_keywords.setPlainText(display_text)
            self.text_keywords.setProperty("raw_keywords", "\n".join(raw_keywords_list))
        else:
            self.text_keywords.setPlainText("未找到相关的关键词信息。")
            self.text_keywords.setProperty("raw_keywords", "")
            
    def on_reverse_search(self):
        query = self.input_kw.text().strip()
        if not query:
            QMessageBox.warning(self, "错误", "请输入关键词")
            return
            
        status, matches = self.engine.reverse_search(query)
        if status == "ok" and matches:
            display_text = f"【反查关键词】: {query}\n\n"
            for m in matches if isinstance(matches, list) else []:
                src = m.get('source', '')
                page = m.get('page', '')
                ctx = m.get('context_text', '').replace('\n', ' ')
                ipc = m.get('ipc_text', '').replace('\n', ' ')
                
                title_str = ""
                if src:
                    title_str += f"《{src.replace('.pdf', '')}》"
                if page:
                    title_str += f"-第{page}页"
                    
                display_text += f"{title_str}-{ctx}-\"{ipc}\"\n"
                display_text += "-" * 40 + "\n"
                
            self.text_keywords.setPlainText(display_text)
            self.text_keywords.setProperty("raw_keywords", query)
        else:
            self.text_keywords.setPlainText(matches if isinstance(matches, str) else "未找到相关的分类信息。")
            self.text_keywords.setProperty("raw_keywords", "")
            
    def on_analyze(self):
        api_key = self.api_key_input.text().strip()
        self.settings.setValue('api_key', api_key)
        
        keywords_text = self.text_keywords.property("raw_keywords")
        user_text = self.input_text.toPlainText().strip()
        
        if not api_key:
            QMessageBox.warning(self, "错误", "请先在上方填入 DeepSeek API Key")
            return
        if not keywords_text:
            QMessageBox.warning(self, "错误", "请先通过搜索提取出有用的关键词哦")
            return
        if not user_text:
            QMessageBox.warning(self, "错误", "请输入需要分析的文本内容")
            return
            
        self.set_gui_enabled(False)
        self.text_result.setPlainText("正在调用 DeepSeek 分析中，请稍候...")
        
        self.worker = WorkerThread(analyze_with_deepseek, api_key, keywords_text, user_text)
        self.worker.finished.connect(self.on_analyze_finished)
        self.worker.error.connect(self.on_error)
        self.worker.start()
        
    def on_analyze_finished(self, result):
        self.set_gui_enabled(True)
        self.text_result.setPlainText(result)
        
    def on_error(self, err_msg):
        self.set_gui_enabled(True)
        QMessageBox.critical(self, "系统报错", f"发生错误:\n{err_msg}")


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
