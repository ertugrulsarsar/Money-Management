import logging
import json
from datetime import datetime
import os
from typing import Any, Dict
from pathlib import Path

class FinanceLogger:
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(exist_ok=True)
        
        # Log dosyası adı (günlük)
        self.log_file = self.log_dir / f"finance_{datetime.now().strftime('%Y%m%d')}.log"
        
        # Logger'ı yapılandır
        self.logger = logging.getLogger("FinanceLogger")
        self.logger.setLevel(logging.INFO)
        
        # Dosya handler'ı
        file_handler = logging.FileHandler(self.log_file, encoding='utf-8')
        file_handler.setLevel(logging.INFO)
        
        # Format
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        
        # Handler'ı ekle
        self.logger.addHandler(file_handler)
        
        # Yedekleme dizini
        self.backup_dir = self.log_dir / "backups"
        self.backup_dir.mkdir(exist_ok=True)

    def log_user_action(self, user_id: int, action: str, data: Dict[str, Any]) -> None:
        """Kullanıcı işlemlerini loglar."""
        log_data = {
            "user_id": user_id,
            "action": action,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        self.logger.info(f"USER_ACTION: {json.dumps(log_data, ensure_ascii=False)}")
        self._create_backup("user_actions", log_data)

    def log_transaction(self, user_id: int, action: str, data: Dict[str, Any]) -> None:
        """İşlem loglarını kaydeder."""
        log_data = {
            "user_id": user_id,
            "action": action,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        self.logger.info(f"TRANSACTION: {json.dumps(log_data, ensure_ascii=False)}")
        self._create_backup("transactions", log_data)

    def log_budget(self, user_id: int, action: str, data: Dict[str, Any]) -> None:
        """Bütçe loglarını kaydeder."""
        log_data = {
            "user_id": user_id,
            "action": action,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        self.logger.info(f"BUDGET: {json.dumps(log_data, ensure_ascii=False)}")
        self._create_backup("budgets", log_data)

    def log_goal(self, user_id: int, action: str, data: Dict[str, Any]) -> None:
        """Hedef loglarını kaydeder."""
        log_data = {
            "user_id": user_id,
            "action": action,
            "data": data,
            "timestamp": datetime.now().isoformat()
        }
        
        self.logger.info(f"GOAL: {json.dumps(log_data, ensure_ascii=False)}")
        self._create_backup("goals", log_data)

    def _create_backup(self, category: str, data: Dict[str, Any]) -> None:
        """JSON formatında yedek oluşturur."""
        backup_file = self.backup_dir / f"{category}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        
        with open(backup_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def get_transaction_history(self, user_id: int, start_date: datetime = None, end_date: datetime = None) -> list:
        """Belirli bir kullanıcının işlem geçmişini getirir."""
        transactions = []
        log_files = sorted(self.log_dir.glob("finance_*.log"))
        
        for log_file in log_files:
            with open(log_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if "TRANSACTION:" in line:
                        try:
                            log_data = json.loads(line.split("TRANSACTION: ")[1])
                            if log_data["user_id"] == user_id:
                                if start_date and datetime.fromisoformat(log_data["timestamp"]) < start_date:
                                    continue
                                if end_date and datetime.fromisoformat(log_data["timestamp"]) > end_date:
                                    continue
                                transactions.append(log_data)
                        except:
                            continue
        
        return transactions

    def restore_from_backup(self, backup_file: str) -> Dict[str, Any]:
        """Yedekten veri geri yükler."""
        with open(backup_file, 'r', encoding='utf-8') as f:
            return json.load(f)

    def get_latest_backup(self, category: str) -> str:
        """En son yedek dosyasını bulur."""
        backups = sorted(self.backup_dir.glob(f"{category}_*.json"))
        return str(backups[-1]) if backups else None 