from datetime import datetime


class ComicLogger:
    """统一日志"""
    
    @staticmethod
    def info(msg, step=""):
        timestamp = datetime.now().strftime("%H:%M:%S")
        if step:
            print(f"[{timestamp}] 📌 {step}: {msg}")
        else:
            print(f"[{timestamp}] {msg}")
    
    @staticmethod
    def success(msg, step=""):
        timestamp = datetime.now().strftime("%H:%M:%S")
        if step:
            print(f"[{timestamp}] ✅ {step}: {msg}")
        else:
            print(f"[{timestamp}] ✅ {msg}")
    
    @staticmethod
    def error(msg, step=""):
        timestamp = datetime.now().strftime("%H:%M:%S")
        if step:
            print(f"[{timestamp}] ❌ {step}: {msg}")
        else:
            print(f"[{timestamp}] ❌ {msg}")
    
    @staticmethod
    def warn(msg, step=""):
        timestamp = datetime.now().strftime("%H:%M:%S")
        if step:
            print(f"[{timestamp}] ⚠️ {step}: {msg}")
        else:
            print(f"[{timestamp}] ⚠️ {msg}")
    
    @staticmethod
    def header(title):
        print("\n" + "=" * 60)
        print(f"   {title}")
        print("=" * 60)