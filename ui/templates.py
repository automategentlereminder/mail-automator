import json
import sqlite3
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QScrollArea
from PySide6.QtGui import QGuiApplication
from qfluentwidgets import (TitleLabel, SubtitleLabel, LineEdit, TextEdit, 
                            PrimaryPushButton, PushButton, CardWidget, InfoBar, InfoBarPosition,
                            ComboBox, MessageBox, ToolButton, FluentIcon, CheckBox, BodyLabel)
from core.database import DB_PATH

class TemplatesInterface(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent=parent)
        self.setObjectName("TemplatesInterface")
        self.vBoxLayout = QVBoxLayout(self)
        self.vBoxLayout.setContentsMargins(24, 24, 24, 24)
        self.vBoxLayout.setSpacing(16)
        
        headerLayout = QHBoxLayout()
        self.titleLabel = TitleLabel("Templates", self)
        headerLayout.addWidget(self.titleLabel)
        headerLayout.addStretch(1)
        self.guideBtn = PushButton("📖 Guide", self)
        self.guideBtn.clicked.connect(self.show_guide)
        headerLayout.addWidget(self.guideBtn)
        self.vBoxLayout.addLayout(headerLayout)
        
        # Loader
        self.loadLayout = QHBoxLayout()
        self.templateCombo = ComboBox(self)
        self.templateCombo.setPlaceholderText("Select a Template to Edit...")
        self.loadBtn = PushButton("Load", self)
        self.loadBtn.clicked.connect(self.load_template)
        self.newBtn = PushButton("New Template", self)
        self.newBtn.clicked.connect(self.new_template)
        
        self.promptBtn = ToolButton(FluentIcon.ROBOT, self)
        self.promptBtn.setToolTip("Generate AI Prompt")
        self.promptBtn.clicked.connect(self.show_prompt_dialog)
        
        self.loadLayout.addWidget(self.templateCombo)
        self.loadLayout.addWidget(self.loadBtn)
        self.loadLayout.addWidget(self.newBtn)
        self.loadLayout.addWidget(self.promptBtn)
        self.loadLayout.addStretch(1)
        self.vBoxLayout.addLayout(self.loadLayout)
        
        self._setup_editor()
        
        self.vBoxLayout.addStretch(1)
        self.refresh_combo()

    def _setup_editor(self):
        self.editorCard = CardWidget(self)
        layout = QVBoxLayout(self.editorCard)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)
        
        self.current_id = None
        
        self.nameEdit = LineEdit(self.editorCard)
        self.nameEdit.setPlaceholderText("Template Name (e.g., Intro Outreach)")
        layout.addWidget(self.nameEdit)
        
        self.subjectEdit = LineEdit(self.editorCard)
        self.subjectEdit.setPlaceholderText("Subject {{CSV:Name}}...")
        layout.addWidget(self.subjectEdit)
        
        # Variants Area
        self.variantsLayout = QVBoxLayout()
        self.variants = [] # List of TextEdits
        
        self.addVariantBtn = PushButton("Add Variant", self.editorCard)
        self.addVariantBtn.clicked.connect(lambda: self.add_variant_editor())
        layout.addWidget(self.addVariantBtn)
        
        # Initial variant
        self.add_variant_editor()
        
        layout.addLayout(self.variantsLayout)
        
        # Save
        self.saveBtn = PrimaryPushButton("Save Template", self.editorCard)
        self.saveBtn.clicked.connect(self.save_template)
        layout.addWidget(self.saveBtn, alignment=Qt.AlignRight)
        
        self.vBoxLayout.addWidget(self.editorCard)

    def add_variant_editor(self, text=""):
        if isinstance(text, bool):
            text = ""
        idx = len(self.variants) + 1
        editor = TextEdit(self.editorCard)
        editor.setPlaceholderText(f"Variant {idx} Body... Use {{{{CSV:Column}}}} and {{Spintax|Options}}")
        editor.setMinimumHeight(120)
        editor.setPlainText(text)
        self.variants.append(editor)
        self.variantsLayout.addWidget(editor)

    def clear_variants(self):
        for editor in self.variants:
            self.variantsLayout.removeWidget(editor)
            editor.deleteLater()
        self.variants = []

    def refresh_combo(self):
        self.templateCombo.clear()
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute("SELECT id, name FROM templates")
            for tid, name in cur.fetchall():
                self.templateCombo.addItem(name, userData=tid)
            conn.close()
        except:
            pass

    def new_template(self):
        self.current_id = None
        self.nameEdit.clear()
        self.subjectEdit.clear()
        self.clear_variants()
        self.add_variant_editor()

    def load_template(self):
        if self.templateCombo.currentIndex() < 0:
            return
            
        tid = self.templateCombo.currentData()
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            cur.execute("SELECT id, name, subject, variants FROM templates WHERE id=?", (tid,))
            row = cur.fetchone()
            conn.close()
            
            if row:
                self.current_id = row[0]
                self.nameEdit.setText(row[1])
                self.subjectEdit.setText(row[2])
                self.clear_variants()
                
                variants_str = row[3]
                try:
                    v_list = json.loads(variants_str)
                    for v in v_list:
                        self.add_variant_editor(v)
                except:
                    self.add_variant_editor()
        except:
            pass

    def save_template(self):
        name = self.nameEdit.text().strip()
        subject = self.subjectEdit.text().strip()
        
        if not name or not subject:
            InfoBar.error("Error", "Name and Subject are required.", parent=self.window())
            return
            
        v_list = [v.toPlainText() for v in self.variants if v.toPlainText().strip()]
        if not v_list:
            InfoBar.error("Error", "At least one valid variant body is required.", parent=self.window())
            return
            
        variants_json = json.dumps(v_list)
        
        try:
            conn = sqlite3.connect(DB_PATH)
            cur = conn.cursor()
            
            if self.current_id:
                cur.execute("UPDATE templates SET name=?, subject=?, body=?, variants=? WHERE id=?",
                            (name, subject, v_list[0], variants_json, self.current_id))
            else:
                cur.execute("INSERT INTO templates (name, subject, body, variants) VALUES (?, ?, ?, ?)",
                            (name, subject, v_list[0], variants_json))
                self.current_id = cur.lastrowid
                
            conn.commit()
            conn.close()
            
            InfoBar.success("Success", "Template saved successfully.", parent=self.window())
            self.refresh_combo()
        except sqlite3.IntegrityError:
            InfoBar.error("Error", "Template with this name already exists.", parent=self.window())
        except Exception as e:
            InfoBar.error("Error", f"Failed to save: {e}", parent=self.window())

    def show_guide(self):
        content = (
            "<b>Templates Builder</b><br><br>"
            "Create reusable email blueprints here.<br><br>"
            "• <b>Variables:</b> Use `{{CSV:ColumnName}}` to pull data from your Excel/CSV files. You can also specify fallbacks like `{{CSV:FirstName|there}}`.<br>"
            "• <b>Spintax:</b> Enclose options like `{Hello|Hi|Hey}`. A random option will be chosen for each email, dodging spam filters.<br>"
            "• <b>Variants:</b> Click 'Add Variant' to create completely different bodies for your pitch. The tool will distribute these evenly (Round-Robin) to your queue."
        )
        msgBox = MessageBox("Templates Guide", content, self.window())
        msgBox.yesButton.setText("Got it!")
        msgBox.cancelButton.hide()
        msgBox.exec()

    def show_prompt_dialog(self):
        dialog = AIPromptDialog(self.window())
        dialog.exec()


class AIPromptDialog(MessageBox):
    def __init__(self, parent=None):
        super().__init__("AI Prompt Assistant", "", parent)
        self.cancelButton.hide()
        self.yesButton.setText("Close")
        
        # Add a copy button in the button layout
        self.copyBtn = PrimaryPushButton("Copy Prompt")
        self.buttonLayout.insertWidget(1, self.copyBtn)
        self.copyBtn.clicked.connect(self.copy_prompt)
        
        # In newer qfluentwidgets MessageBox, we append to textLayout
        # Let's create a custom container widget to hold our prompt UI
        self.customWidget = QWidget()
        self.customWidget.setMinimumWidth(500)
        self.customLayout = QVBoxLayout(self.customWidget)
        self.customLayout.setContentsMargins(0, 16, 0, 0)
        self.customLayout.setSpacing(16)
        
        intro = BodyLabel("Copy this prompt, replace the placeholders with your actual message intent, and paste it into ChatGPT, Claude, or Gemini to get Spintax-ready variations.")
        intro.setWordWrap(True)
        self.customLayout.addWidget(intro)
        
        # Modifiers
        self.modLayout = QHBoxLayout()
        self.noMarketingCb = CheckBox("Avoid Marketing Tone")
        self.shortCb = CheckBox("Keep it Short & Concise")
        self.casualCb = CheckBox("Friendly & Casual")
        self.modLayout.addWidget(self.noMarketingCb)
        self.modLayout.addWidget(self.shortCb)
        self.modLayout.addWidget(self.casualCb)
        self.customLayout.addLayout(self.modLayout)
        
        # Connections
        self.noMarketingCb.stateChanged.connect(self.update_prompt)
        self.shortCb.stateChanged.connect(self.update_prompt)
        self.casualCb.stateChanged.connect(self.update_prompt)
        
        # Prompt Box
        self.promptBox = TextEdit(self.customWidget)
        self.promptBox.setMinimumHeight(200)
        self.promptBox.setReadOnly(True)
        self.customLayout.addWidget(self.promptBox)
        
        # Add our custom widget to the MessageBox's main textLayout
        self.textLayout.addWidget(self.customWidget)
        
        self.update_prompt()
        
    def update_prompt(self):
        modifiers = []
        if self.noMarketingCb.isChecked():
            modifiers.append("Avoid any salesy, pushy, or marketing jargon.")
        if self.shortCb.isChecked():
            modifiers.append("Keep the text short, concise, and straight to the point.")
        if self.casualCb.isChecked():
            modifiers.append("Use a friendly, casual, and conversational tone.")
            
        mods_text = " ".join(modifiers)
        
        base_prompt = f"""I am creating an email outreach campaign and I need you to generate 3 different body variants and 1 subject line using Spintax format.

**Rules for Output:**
1. Use Spintax format like {{word1|word2|word3}} to randomize words and phrases heavily.
2. Provide exactly 1 highly spinnable Subject line.
3. Provide exactly 3 separate spinnable Body variants (Variant 1, Variant 2, Variant 3).
{mods_text}

---
**Write what you want to say below:**

[Write your message intent here, e.g., "Hi, I'm John from GentleReminder. We help automate outbound emails. Do you have 5 minutes next week?"]
"""
        self.promptBox.setPlainText(base_prompt)
        
    def copy_prompt(self):
        clipboard = QGuiApplication.clipboard()
        clipboard.setText(self.promptBox.toPlainText())
        InfoBar.success("Copied", "Prompt copied to clipboard!", parent=self.window())

