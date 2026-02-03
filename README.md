# 🌐 Lingo-Live

**Lingo-Live** is a powerful, real-time screen translation tool designed for seamless multilingual experiences on your desktop. Run it in the background, select any text on your screen (images, PDFs, videos), and get instant translations, summaries, and audio readouts—all without leaving your current window.

![Lingo-Live Banner](https://via.placeholder.com/800x200.png?text=Lingo-Live:+Real-Time+Screen+Translation)

---

## ✨ Features

- **📷 OCR & Translation**: Instantly capture any screen region and translate text using advanced OCR (Tesseract) and translation APIs (Lingo.dev optimized).
- **🔊 Text-to-Speech (TTS)**: Listen to translations with high-quality, natural-sounding voices (via Microsoft Edge TTS).
- **✨ AI Summarization**: Get concise summaries of long translations using **Google Gemini 1.5 Flash**.
- **⚙️ Modern Settings UI**: Customize your experience with a beautiful, user-friendly settings panel built with CustomTkinter.
- **🛡️ Persistent & Unintrusive**: Runs quietly in the background. Toggle visibility instantly or minimize to tray (conceptual).
- **⌨️ Global Hotkeys**: Trigger translations from anywhere with `Ctrl+Alt+T` (customizable).
- **🎨 Theming**: Auto-adapts to your system theme (Dark/Light).

---

## 🛠️ Installation

### Prerequisites
1. **Python 3.8+** installed.
2. **Tesseract OCR** installed:
   - [Windows Installer](https://github.com/UB-Mannheim/tesseract/wiki)
   - Add Tesseract to your PATH or configure it in Settings.

### Steps
1. **Clone the repository**:
   ```bash
   git clone https://github.com/your-username/lingo-live.git
   cd lingo-live
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```
   *Note: Ensure `edge-tts` and `pygame` are installed for TTS features.*

3. **Run the Application**:
   ```bash
   python main.py
   ```
   *Or use `run.bat` for quick launch.*

---

## 🚀 Usage

1. **Start Lingo-Live**: The app will launch and run in the background.
2. **Select Text**:
   - Press **`Ctrl+Alt+T`** (default hotkey).
   - The screen will dim. Click and drag to select the text you want to translate.
3. **View Results**: The overlay window will appear with the captured text and its translation.
4. **Interact**:
   - 🔊 **Read Aloud**: Click the speaker icon to hear the translation.
   - ✨ **Summarize**: Click the sparkle icon to get a summary.
   - 📷 **New**: Click to capture a new area.
   - ✖ **Hide**: Click 'X' or press `Esc` to hide the window (app keeps running).
5. **Settings**: Click the ⚙️ icon to change hotkeys, languages, opacity, and API keys.

---

## 🏗️ System Architecture

### 🧩 Block Diagram

This high-level diagram shows how different modules interact within Lingo-Live.

```mermaid
graph TD
    User((👤 User))
    
    subgraph "Lingo-Live System"
        UI[🖥️ CustomTkinter UI]
        HK[⌨️ Hotkey Listener]
        
        subgraph "Core Services"
            Cap[📷 Screen Capture (MSS)]
            OCR[🔍 OCR Engine (Tesseract)]
            Trans[🌐 Translation Service]
            Sum[✨ Summarization (Gemini)]
            TTS[🔊 TTS Service (Edge TTS)]
        end
        
        Config[⚙️ Settings Manager]
    end
    
    Ext[☁️ External APIs]
    
    User -->|Ctrl+Alt+T| HK
    User -->|Interacts| UI
    
    HK -->|Trigger| Cap
    UI -->|Request| Cap
    
    Cap -->|Image| OCR
    OCR -->|Text| Trans
    
    Trans -->|Lingo.dev / Google| Ext
    Trans -->|Translated Text| UI
    
    UI -->|Summarize Request| Sum
    Sum -->|Text| UI
    
    UI -->|Read Aloud Request| TTS
    TTS -->|Audio| User
    
    Config -->|Load/Save| UI
    Config -.->|Configure| Trans
    Config -.->|Configure| Sum
```

---

### 🔄 Execution Flowchart

The following flowchart illustrates the step-by-step process from user activation to displaying the result.

```mermaid
flowchart TD
    Start([🚀 Start App]) --> Init[Initialize Services & UI]
    Init --> BgLoop{Wait for Input}
    
    BgLoop -->|Hotkey / 'New' Btn| SelectStart[Start Selection Mode]
    
    SelectStart --> UserSelect[👤 User Selects Area]
    UserSelect --> Capture[📷 Capture Screenshot]
    
    Capture --> OCRProcess[🔍 Extract Text (OCR)]
    
    OCRProcess -->|Text Found?| CheckText{Text Found?}
    CheckText -- No --> ErrMsg[Show 'No Text' Error] --> BgLoop
    CheckText -- Yes --> Translate[🌐 Translate Text]
    
    Translate --> Display[🖥️ Show Result in Overlay]
    
    Display --> UserAction{User Action}
    
    UserAction -- Listen --> GenTTS[🔊 Generate Audio (TTS)] --> PlayTTS[Play Audio] --> UserAction
    UserAction -- Summarize --> GenSum[✨ Call Gemini API] --> ShowSum[Append Summary] --> UserAction
    UserAction -- Hide/Close --> Hide[✖ Hide Window] --> BgLoop
```

---

## 📜 License

Distributed under the MIT License. See `LICENSE` for more information.

---

Created with ❤️ for seamless browsing.
