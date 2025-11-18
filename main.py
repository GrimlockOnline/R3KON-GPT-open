import tkinter as tk
from tkinter import scrolledtext, ttk, messagebox
from threading import Thread
import json
import os
import re
from datetime import datetime
import sys

# PyInstaller compatibility - Get base path
def get_base_path():
    """Get base path for resources (works with PyInstaller)"""
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    else:
        return os.path.dirname(os.path.abspath(__file__))

BASE_PATH = get_base_path()

# Import llama_cpp with error handling
try:
    from llama_cpp import Llama
    LLAMA_AVAILABLE = True
except ImportError as e:
    LLAMA_AVAILABLE = False
    print(f"Warning: llama_cpp not available: {e}")

# Configuration files in user directory
CONFIG_FILE = os.path.join(os.path.expanduser("~"), "rekon_config.json")
MEMORY_FILE = os.path.join(os.path.expanduser("~"), "rekon_memory.json")

class R3KONGPT:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("R3KON GPT - Cybersecurity Assistant")
        self.root.geometry("1200x800")
        self.root.minsize(900, 600)
        
        # Set icon
        try:
            icon_path = os.path.join(BASE_PATH, "icon.ico")
            if os.path.exists(icon_path):
                self.root.iconbitmap(icon_path)
        except:
            pass
        
        # Load configuration
        self.config = self.load_config()
        self.conversation_history = []
        self.session_memory = []
        self.persistent_memory = self.load_memory()
        
        # Model state
        self.llm = None
        self.model_loaded = False
        self.model_error = None
        
        # System prompt
        self.SYSTEM_PROMPT = (
            "You are R3KON GPT, a professional cybersecurity assistant. "
            "CRITICAL RULES:\n"
            "1. ALWAYS respond in English only. Never use Chinese or any other language.\n"
            "2. Stay strictly on topic related to cybersecurity, programming, or the user's question.\n"
            "3. Keep responses clear, concise, and professional.\n"
            "4. Use structured formatting: bullet points, numbered lists, or paragraphs as appropriate.\n"
            "5. Never repeat yourself or generate repetitive content.\n"
            "6. If asked something off-topic, politely redirect to cybersecurity topics.\n"
        )
        
        # Setup UI
        self.setup_ui()
        self.apply_theme()
        
        # Load model in background
        if LLAMA_AVAILABLE:
            Thread(target=self.load_model, daemon=True).start()
        else:
            self.add_system_message("❌ Error: llama-cpp-python not installed.\n")
        
    def load_config(self):
        """Load user configuration"""
        default_config = {
            "theme": "dark",
            "font_size": 11,
            "font_family": "Segoe UI",
            "response_length": "medium",
            "session_memory": True,
            "persistent_memory": False,
            "max_history": 10
        }
        
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    loaded = json.load(f)
                    return {**default_config, **loaded}
            except:
                return default_config
        return default_config
    
    def save_config(self):
        """Save configuration"""
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=2)
        except:
            pass
    
    def load_memory(self):
        """Load persistent memory"""
        if os.path.exists(MEMORY_FILE):
            try:
                with open(MEMORY_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}
    
    def save_memory(self):
        """Save persistent memory"""
        try:
            with open(MEMORY_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.persistent_memory, f, indent=2)
        except:
            pass
    
    def load_model(self):
        """Load the LLM model"""
        try:
            self.add_system_message("⏳ Loading R3KON GPT model...")
            
            # Find model file - check multiple locations
            model_filename = "qwen1.5-1.8b-chat-q4_k_m.gguf"
            
            possible_paths = [
                os.path.join(BASE_PATH, "model", model_filename),
                os.path.join(BASE_PATH, model_filename),
                os.path.join(os.path.dirname(sys.executable), "model", model_filename),
                os.path.join(os.getcwd(), "model", model_filename),
            ]
            
            model_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    model_path = path
                    break
            
            if model_path is None:
                raise FileNotFoundError(
                    f"Model file not found. Please ensure the model is in the 'model' folder."
                )
            
            # Load model
            self.llm = Llama(
                model_path=model_path,
                n_ctx=4096,
                n_threads=6,
                verbose=False
            )
            
            self.model_loaded = True
            self.add_system_message("✅ Model loaded successfully! Ask me anything about cybersecurity.\n")
            
        except Exception as e:
            self.model_error = str(e)
            self.model_loaded = False
            self.add_system_message(f"❌ Error loading model: {e}\n")
    
    def setup_ui(self):
        """Setup user interface"""
        
        # Main container
        main_frame = tk.Frame(self.root)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Left sidebar
        self.sidebar = tk.Frame(main_frame, width=200, relief=tk.RAISED, borderwidth=1)
        self.sidebar.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 2))
        self.sidebar.pack_propagate(False)
        
        # Sidebar title
        sidebar_title = tk.Label(self.sidebar, text="⚙️ SETTINGS", font=("Arial", 12, "bold"))
        sidebar_title.pack(pady=10)
        
        # Theme toggle
        tk.Label(self.sidebar, text="Theme:").pack(pady=(10, 2))
        theme_frame = tk.Frame(self.sidebar)
        theme_frame.pack()
        tk.Button(theme_frame, text="🌙 Dark", command=lambda: self.change_theme("dark"), width=8).pack(side=tk.LEFT, padx=2)
        tk.Button(theme_frame, text="☀️ Light", command=lambda: self.change_theme("light"), width=8).pack(side=tk.LEFT, padx=2)
        
        # Font size
        tk.Label(self.sidebar, text="Font Size:").pack(pady=(15, 2))
        font_frame = tk.Frame(self.sidebar)
        font_frame.pack()
        tk.Button(font_frame, text="A-", command=lambda: self.adjust_font(-1), width=5).pack(side=tk.LEFT, padx=2)
        tk.Button(font_frame, text="A+", command=lambda: self.adjust_font(1), width=5).pack(side=tk.LEFT, padx=2)
        
        # Response length
        tk.Label(self.sidebar, text="Response Length:").pack(pady=(15, 2))
        self.length_var = tk.StringVar(value=self.config["response_length"])
        length_menu = ttk.Combobox(
            self.sidebar,
            textvariable=self.length_var,
            values=["short", "medium", "long"],
            state="readonly",
            width=12
        )
        length_menu.pack()
        length_menu.bind("<<ComboboxSelected>>", lambda e: self.update_config("response_length", self.length_var.get()))
        
        # Memory toggles
        tk.Label(self.sidebar, text="Memory:").pack(pady=(15, 2))
        self.session_mem_var = tk.BooleanVar(value=self.config["session_memory"])
        tk.Checkbutton(
            self.sidebar,
            text="Session Memory",
            variable=self.session_mem_var,
            command=lambda: self.update_config("session_memory", self.session_mem_var.get())
        ).pack()
        
        self.persist_mem_var = tk.BooleanVar(value=self.config["persistent_memory"])
        tk.Checkbutton(
            self.sidebar,
            text="Persistent Memory",
            variable=self.persist_mem_var,
            command=lambda: self.update_config("persistent_memory", self.persist_mem_var.get())
        ).pack()
        
        # Quick actions
        tk.Label(self.sidebar, text="Quick Actions:", font=("Arial", 10, "bold")).pack(pady=(20, 5))
        tk.Button(self.sidebar, text="📋 Clear Chat", command=self.clear_chat, width=15).pack(pady=2)
        tk.Button(self.sidebar, text="💾 Export Chat", command=self.export_chat, width=15).pack(pady=2)
        tk.Button(self.sidebar, text="🗑️ Clear Memory", command=self.clear_memory, width=15).pack(pady=2)
        
        # Right side - chat area
        chat_container = tk.Frame(main_frame)
        chat_container.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        # Header
        header = tk.Frame(chat_container, height=60, relief=tk.RAISED, borderwidth=1)
        header.pack(fill=tk.X)
        header.pack_propagate(False)
        
        title_label = tk.Label(header, text="🛡️ R3KON GPT", font=("Arial", 18, "bold"))
        title_label.pack(side=tk.LEFT, padx=20, pady=10)
        
        subtitle_label = tk.Label(header, text="Professional Cybersecurity Assistant", font=("Arial", 10))
        subtitle_label.pack(side=tk.LEFT, pady=10)
        
        # Chat display
        chat_frame = tk.Frame(chat_container)
        chat_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.chat_box = scrolledtext.ScrolledText(
            chat_frame,
            wrap=tk.WORD,
            font=(self.config["font_family"], self.config["font_size"]),
            relief=tk.FLAT,
            padx=10,
            pady=10
        )
        self.chat_box.pack(fill=tk.BOTH, expand=True)
        self.chat_box.configure(state="disabled")
        
        # Text tags
        self.chat_box.tag_config("user", foreground="#00A3FF", font=(self.config["font_family"], self.config["font_size"], "bold"))
        self.chat_box.tag_config("assistant", foreground="#00FF88", font=(self.config["font_family"], self.config["font_size"], "bold"))
        self.chat_box.tag_config("system", foreground="#FFB800", font=(self.config["font_family"], self.config["font_size"], "italic"))
        self.chat_box.tag_config("error", foreground="#FF4444")
        self.chat_box.tag_config("thinking", foreground="#888888", font=(self.config["font_family"], self.config["font_size"], "italic"))
        
        # Quick commands
        quick_cmd_frame = tk.Frame(chat_container)
        quick_cmd_frame.pack(fill=tk.X, padx=10)
        
        tk.Button(
            quick_cmd_frame,
            text="📝 Summarize",
            command=lambda: self.quick_command("summarize"),
            relief=tk.FLAT,
            padx=10
        ).pack(side=tk.LEFT, padx=2, pady=5)
        
        tk.Button(
            quick_cmd_frame,
            text="🔍 Explain Simply",
            command=lambda: self.quick_command("explain"),
            relief=tk.FLAT,
            padx=10
        ).pack(side=tk.LEFT, padx=2, pady=5)
        
        # Input area
        input_frame = tk.Frame(chat_container)
        input_frame.pack(fill=tk.X, padx=10, pady=(0, 10))
        
        self.entry = tk.Entry(
            input_frame,
            font=(self.config["font_family"], self.config["font_size"]),
            relief=tk.FLAT,
            borderwidth=2
        )
        self.entry.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, ipady=8, padx=(0, 5))
        self.entry.bind("<Return>", self.send_message)
        self.entry.focus_set()
        
        self.send_btn = tk.Button(
            input_frame,
            text="Send ▶",
            command=self.send_message,
            font=("Arial", 10, "bold"),
            relief=tk.FLAT,
            padx=20,
            pady=8
        )
        self.send_btn.pack(side=tk.RIGHT)
        
        # Status bar
        self.status_bar = tk.Label(chat_container, text="Ready", relief=tk.SUNKEN, anchor=tk.W)
        self.status_bar.pack(fill=tk.X, side=tk.BOTTOM)
    
    def apply_theme(self):
        """Apply color theme"""
        if self.config["theme"] == "dark":
            bg_color = "#1E1E1E"
            fg_color = "#FFFFFF"
            input_bg = "#2D2D2D"
            sidebar_bg = "#252526"
            btn_bg = "#0E639C"
        else:
            bg_color = "#FFFFFF"
            fg_color = "#000000"
            input_bg = "#F5F5F5"
            sidebar_bg = "#E5E5E5"
            btn_bg = "#0078D4"
        
        self.root.configure(bg=bg_color)
        self.sidebar.configure(bg=sidebar_bg)
        self.chat_box.configure(bg=bg_color, fg=fg_color, insertbackground=fg_color)
        self.entry.configure(bg=input_bg, fg=fg_color, insertbackground=fg_color)
        self.send_btn.configure(bg=btn_bg, fg="#FFFFFF", activebackground=btn_bg)
        
        # Update sidebar widgets
        for widget in self.sidebar.winfo_children():
            if isinstance(widget, tk.Label):
                widget.configure(bg=sidebar_bg, fg=fg_color)
            elif isinstance(widget, tk.Frame):
                widget.configure(bg=sidebar_bg)
                for child in widget.winfo_children():
                    if isinstance(child, tk.Button):
                        child.configure(bg=btn_bg, fg="#FFFFFF", activebackground=btn_bg)
    
    def change_theme(self, theme):
        """Change UI theme"""
        self.config["theme"] = theme
        self.save_config()
        self.apply_theme()
    
    def adjust_font(self, delta):
        """Adjust font size"""
        self.config["font_size"] = max(8, min(18, self.config["font_size"] + delta))
        self.save_config()
        self.chat_box.configure(font=(self.config["font_family"], self.config["font_size"]))
        self.entry.configure(font=(self.config["font_family"], self.config["font_size"]))
    
    def update_config(self, key, value):
        """Update configuration"""
        self.config[key] = value
        self.save_config()
    
    def add_system_message(self, message):
        """Add system message"""
        self.chat_box.configure(state="normal")
        self.chat_box.insert(tk.END, f"{message}\n", "system")
        self.chat_box.see(tk.END)
        self.chat_box.configure(state="disabled")
        self.root.update_idletasks()
    
    def add_message(self, sender, message, tag=""):
        """Add message with formatting"""
        self.chat_box.configure(state="normal")
        timestamp = datetime.now().strftime("%H:%M")
        
        if sender == "You":
            self.chat_box.insert(tk.END, f"\n{sender} [{timestamp}]:\n", "user")
        elif sender == "R3KON GPT":
            self.chat_box.insert(tk.END, f"\n{sender} [{timestamp}]:\n", "assistant")
        else:
            self.chat_box.insert(tk.END, f"\n{sender}:\n", tag if tag else "system")
        
        self.chat_box.insert(tk.END, f"{message}\n")
        self.chat_box.see(tk.END)
        self.chat_box.configure(state="disabled")
    
    def show_thinking(self):
        """Show thinking indicator"""
        self.chat_box.configure(state="normal")
        self.chat_box.insert(tk.END, "\n⏳ R3KON GPT is thinking...\n", "thinking")
        self.chat_box.see(tk.END)
        self.chat_box.configure(state="disabled")
        self.status_bar.config(text="Generating response...")
        self.root.update_idletasks()
    
    def remove_thinking(self):
        """Remove thinking indicator"""
        self.chat_box.configure(state="normal")
        content = self.chat_box.get("1.0", tk.END)
        if "⏳ R3KON GPT is thinking..." in content:
            idx = content.rfind("⏳ R3KON GPT is thinking...")
            if idx != -1:
                lines = content[:idx].count('\n')
                self.chat_box.delete(f"{lines + 1}.0", f"{lines + 2}.0")
        self.chat_box.configure(state="disabled")
        self.status_bar.config(text="Ready")
    
    def filter_response(self, text):
        """Filter and clean response"""
        # Remove Chinese characters
        if re.search(r'[\u4e00-\u9fff]', text):
            return "I apologize, but I can only respond in English. Let me answer your question in English."
        
        # Remove repetition
        lines = text.split('\n')
        unique_lines = []
        for line in lines:
            if line.strip():
                if not unique_lines or line not in unique_lines[-3:]:
                    unique_lines.append(line)
        
        filtered = '\n'.join(unique_lines)
        
        # Trim if too long
        max_length = {"short": 500, "medium": 1000, "long": 2000}
        limit = max_length.get(self.config["response_length"], 1000)
        
        if len(filtered) > limit:
            filtered = filtered[:limit] + "...\n\n(Response trimmed. Ask me to elaborate if needed.)"
        
        return filtered
    
    def build_context(self, user_prompt):
        """Build conversation context"""
        context_parts = [self.SYSTEM_PROMPT]
        
        # Add persistent memory
        if self.config["persistent_memory"] and self.persistent_memory:
            context_parts.append("\n--- User Information ---")
            for key, value in self.persistent_memory.items():
                context_parts.append(f"{key}: {value}")
        
        # Add session memory
        if self.config["session_memory"] and self.session_memory:
            context_parts.append("\n--- Recent Conversation ---")
            for turn in self.session_memory[-self.config["max_history"]:]:
                context_parts.append(f"User: {turn['user']}")
                context_parts.append(f"Assistant: {turn['assistant']}")
        
        context_parts.append(f"\nUser: {user_prompt}")
        context_parts.append("Assistant:")
        
        return '\n'.join(context_parts)
    
    def generate_response(self, prompt):
        """Generate response from model"""
        import time
        start_time = time.time()
        timeout = 180  # 3 minute timeout
        
        try:
            if not self.model_loaded:
                self.remove_thinking()
                self.add_message("Error", "❌ Model not loaded. Please restart the application.", "error")
                return
            
            # Build context with reasonable memory
            context_parts = [self.SYSTEM_PROMPT]
            
            # Keep last 5 conversation turns for context
            if self.config["session_memory"] and self.session_memory:
                context_parts.append("\n--- Recent Conversation ---")
                for turn in self.session_memory[-5:]:
                    context_parts.append(f"User: {turn['user']}")
                    context_parts.append(f"Assistant: {turn['assistant']}")
            
            context_parts.append(f"\nUser: {prompt}")
            context_parts.append("Assistant:")
            full_prompt = '\n'.join(context_parts)
            
            # BALANCED token limits - ChatGPT-like length
            token_limits = {
                "short": 300,    # ~200 words
                "medium": 600,   # ~400 words  
                "long": 1000     # ~650 words
            }
            max_tokens = token_limits.get(self.config["response_length"], 600)
            
            # Generate with optimized settings
            response = self.llm(
                full_prompt,
                max_tokens=max_tokens,
                stop=["User:", "\n\nUser:", "Assistant:"],
                echo=False,
                temperature=0.7,
                top_p=0.9,
                top_k=40,
                repeat_penalty=1.2,
                frequency_penalty=0.3,
                presence_penalty=0.3,
            )
            
            # Check timeout
            elapsed = time.time() - start_time
            if elapsed > timeout:
                bot_reply = "⚠️ Response took too long. Try 'short' or 'medium' response length in settings."
            else:
                bot_reply = response["choices"][0]["text"].strip()
                
                # Only filter Chinese characters, don't trim length
                if re.search(r'[\u4e00-\u9fff]', bot_reply):
                    bot_reply = "I apologize, but I can only respond in English. Let me answer your question in English."
                
                # Remove excessive repetition only
                lines = bot_reply.split('\n')
                unique_lines = []
                for line in lines:
                    if line.strip():
                        # Only skip if exact same line appears 3+ times in a row
                        if not unique_lines or line not in unique_lines[-2:]:
                            unique_lines.append(line)
                
                bot_reply = '\n'.join(unique_lines)
            
            # Update memory (keep last 8)
            if self.config["session_memory"]:
                self.session_memory.append({"user": prompt, "assistant": bot_reply})
                if len(self.session_memory) > 8:
                    self.session_memory.pop(0)
            
        except KeyboardInterrupt:
            bot_reply = "⚠️ Generation cancelled."
        except Exception as e:
            elapsed = time.time() - start_time
            if elapsed > timeout:
                bot_reply = f"⚠️ Timed out after {int(elapsed)}s. Try shorter response length in settings."
            else:
                bot_reply = f"⚠️ Error: {str(e)}"
        
        finally:
            self.remove_thinking()
            self.add_message("R3KON GPT", bot_reply)
    
    def send_message(self, event=None):
        """Send message"""
        user_text = self.entry.get().strip()
        
        if not user_text:
            return
        
        if not self.model_loaded:
            messagebox.showwarning("Model Not Ready", "Please wait for the model to finish loading.")
            return
        
        # Add user message
        self.add_message("You", user_text)
        self.conversation_history.append({"role": "user", "content": user_text})
        
        # Clear input
        self.entry.delete(0, tk.END)
        
        # Show thinking
        self.show_thinking()
        
        # Generate response in background
        Thread(target=self.generate_response, args=(user_text,), daemon=True).start()
    
    def quick_command(self, cmd_type):
        """Execute quick command"""
        if not self.conversation_history or len(self.conversation_history) < 2:
            messagebox.showinfo("No Context", "Please have a conversation first.")
            return
        
        commands = {
            "summarize": "Summarize your last response in 2-3 bullet points.",
            "explain": "Explain your last response in simpler terms."
        }
        
        if cmd_type in commands:
            self.entry.delete(0, tk.END)
            self.entry.insert(0, commands[cmd_type])
            self.send_message()
    
    def clear_chat(self):
        """Clear chat history"""
        if messagebox.askyesno("Clear Chat", "Clear the chat history?"):
            self.chat_box.configure(state="normal")
            self.chat_box.delete("1.0", tk.END)
            self.chat_box.configure(state="disabled")
            self.conversation_history = []
            self.session_memory = []
            self.add_system_message("Chat cleared.\n")
    
    def clear_memory(self):
        """Clear memory"""
        if messagebox.askyesno("Clear Memory", "Clear all stored memory?"):
            self.persistent_memory = {}
            self.save_memory()
            self.session_memory = []
            messagebox.showinfo("Memory Cleared", "All memory cleared successfully.")
    
    def export_chat(self):
        """Export chat"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"rekon_chat_{timestamp}.txt"
            
            content = self.chat_box.get("1.0", tk.END)
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(f"R3KON GPT Chat Export\n")
                f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write("=" * 80 + "\n\n")
                f.write(content)
            
            messagebox.showinfo("Export Success", f"Chat exported to {filename}")
        except Exception as e:
            messagebox.showerror("Export Failed", f"Failed to export: {e}")
    
    def run(self):
        """Run application"""
        self.root.mainloop()

# Entry point
if __name__ == "__main__":
    try:
        app = R3KONGPT()
        app.run()
    except Exception as e:
        try:
            root = tk.Tk()
            root.withdraw()
            messagebox.showerror("Startup Error", f"Failed to start:\n\n{str(e)}")
        except:
            print(f"FATAL ERROR: {e}")
        sys.exit(1)