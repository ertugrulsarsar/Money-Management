import requests
import json
import hashlib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Union
from sqlalchemy.orm import Session
from models.database import User, BankAccount, Transaction
import time

class BankingService:
    def __init__(self, db: Session):
        """
        Bankacılık API entegrasyonu için servis.
        
        Args:
            db: Veritabanı oturumu
        """
        self.db = db
        
        # API anahtarları - gerçek uygulamada çevresel değişkenlerden alınmalı
        self.api_keys = {
            "example_bank": "example_api_key",
            "other_bank": "other_api_key"
        }
        
        # API uç noktaları
        self.api_endpoints = {
            "example_bank": {
                "base_url": "https://api.example-bank.com/v1",
                "accounts": "/accounts",
                "transactions": "/accounts/{account_id}/transactions",
                "balance": "/accounts/{account_id}/balance"
            },
            "other_bank": {
                "base_url": "https://api.other-bank.com/v2",
                "accounts": "/user/accounts",
                "transactions": "/account/{account_id}/transactions",
                "balance": "/account/{account_id}/balance"
            }
        }
        
        # Önbellek için
        self._cache = {}
        self._cache_expiry = {}
        self._cache_ttl = 300  # 5 dakika
    
    def add_bank_account(
        self, 
        user_id: int, 
        bank_name: str, 
        account_number: str, 
        access_token: str, 
        account_name: Optional[str] = None,
        account_type: Optional[str] = None
    ) -> BankAccount:
        """
        Kullanıcıya yeni bir banka hesabı ekler.
        
        Args:
            user_id: Kullanıcı ID
            bank_name: Banka adı
            account_number: Hesap numarası
            access_token: API erişim token'ı (şifrelenecek)
            account_name: Hesap adı (opsiyonel)
            account_type: Hesap tipi (opsiyonel)
            
        Returns:
            Eklenen banka hesabı
        """
        # Access token'ı şifrele
        hashed_token = self._hash_token(access_token)
        
        # Hesap adı yoksa varsayılan ad ata
        if not account_name:
            account_name = f"{bank_name} Hesabı"
        
        # Veritabanına hesap ekle
        bank_account = BankAccount(
            user_id=user_id,
            bank_name=bank_name,
            account_number=account_number,
            account_name=account_name,
            account_type=account_type,
            access_token=hashed_token,
            last_sync=datetime.now()
        )
        
        self.db.add(bank_account)
        self.db.commit()
        self.db.refresh(bank_account)
        
        return bank_account
    
    def get_user_accounts(self, user_id: int) -> List[BankAccount]:
        """
        Kullanıcının banka hesaplarını getirir.
        
        Args:
            user_id: Kullanıcı ID
            
        Returns:
            Banka hesapları listesi
        """
        accounts = self.db.query(BankAccount).filter(BankAccount.user_id == user_id).all()
        return accounts
    
    def sync_account_transactions(
        self, 
        account_id: int, 
        days_back: int = 30
    ) -> Dict:
        """
        Banka hesabı işlemlerini senkronize eder.
        
        Args:
            account_id: Hesap ID
            days_back: Kaç gün geriye gidilecek
            
        Returns:
            Senkronizasyon sonuçları
        """
        account = self.db.query(BankAccount).filter(BankAccount.id == account_id).first()
        if not account:
            raise ValueError("Hesap bulunamadı")
        
        # İlgili bankaya göre API çağrısı yap
        bank_name = account.bank_name
        if bank_name not in self.api_endpoints:
            raise ValueError(f"Desteklenmeyen banka: {bank_name}")
        
        # Önbellekte varsa ve güncel ise, önbellekten döndür
        cache_key = f"transactions_{account_id}"
        if self._is_cached(cache_key):
            return self._get_from_cache(cache_key)
        
        try:
            # Gerçek API çağrısı simülasyonu
            transactions = self._simulate_bank_api_call(account, days_back)
            
            # İşlemleri veritabanına ekle
            new_count = 0
            for transaction in transactions:
                # İşlem daha önce eklenmiş mi kontrol et
                existing = self.db.query(Transaction).filter(
                    Transaction.user_id == account.user_id,
                    Transaction.external_id == transaction["id"],
                    Transaction.source == f"bank_{bank_name}"
                ).first()
                
                if not existing:
                    # Yeni işlem oluştur
                    new_transaction = Transaction(
                        user_id=account.user_id,
                        amount=transaction["amount"],
                        type="income" if transaction["amount"] > 0 else "expense",
                        category=self._guess_category(transaction["description"]),
                        description=transaction["description"],
                        date=transaction["date"],
                        source=f"bank_{bank_name}",
                        external_id=transaction["id"]
                    )
                    
                    self.db.add(new_transaction)
                    new_count += 1
            
            if new_count > 0:
                self.db.commit()
            
            # Son senkronizasyon tarihini güncelle
            account.last_sync = datetime.now()
            self.db.commit()
            
            result = {
                "success": True,
                "account_id": account_id,
                "total_transactions": len(transactions),
                "new_transactions": new_count,
                "last_sync": account.last_sync
            }
            
            # Önbelleğe ekle
            self._add_to_cache(cache_key, result)
            
            return result
        
        except Exception as e:
            return {
                "success": False,
                "account_id": account_id,
                "error": str(e)
            }
    
    def get_account_balance(self, account_id: int) -> Dict:
        """
        Banka hesabının güncel bakiyesini getirir.
        
        Args:
            account_id: Hesap ID
            
        Returns:
            Hesap bakiyesi
        """
        account = self.db.query(BankAccount).filter(BankAccount.id == account_id).first()
        if not account:
            raise ValueError("Hesap bulunamadı")
        
        # Önbellekte varsa ve güncel ise, önbellekten döndür
        cache_key = f"balance_{account_id}"
        if self._is_cached(cache_key):
            return self._get_from_cache(cache_key)
        
        try:
            # Gerçek API çağrısı simülasyonu
            balance_info = self._simulate_balance_api_call(account)
            
            # Önbelleğe ekle
            self._add_to_cache(cache_key, balance_info)
            
            return balance_info
        
        except Exception as e:
            return {
                "success": False,
                "account_id": account_id,
                "error": str(e)
            }
    
    def remove_bank_account(self, account_id: int) -> bool:
        """
        Banka hesabını siler.
        
        Args:
            account_id: Hesap ID
            
        Returns:
            Başarılı olup olmadığı
        """
        account = self.db.query(BankAccount).filter(BankAccount.id == account_id).first()
        if not account:
            raise ValueError("Hesap bulunamadı")
        
        try:
            # Hesabı sil
            self.db.delete(account)
            self.db.commit()
            
            # Önbelleği temizle
            self._clear_cache(f"transactions_{account_id}")
            self._clear_cache(f"balance_{account_id}")
            
            return True
        
        except Exception as e:
            self.db.rollback()
            raise e
    
    def get_account_summary(self, user_id: int) -> Dict:
        """
        Kullanıcının tüm banka hesaplarının özetini getirir.
        
        Args:
            user_id: Kullanıcı ID
            
        Returns:
            Hesap özeti
        """
        accounts = self.get_user_accounts(user_id)
        
        total_balance = 0
        accounts_summary = []
        
        for account in accounts:
            try:
                balance_info = self.get_account_balance(account.id)
                if balance_info.get("success", False):
                    total_balance += balance_info.get("balance", 0)
                    
                    accounts_summary.append({
                        "id": account.id,
                        "bank_name": account.bank_name,
                        "account_name": account.account_name,
                        "account_type": account.account_type,
                        "balance": balance_info.get("balance", 0),
                        "currency": balance_info.get("currency", "TRY"),
                        "last_sync": account.last_sync
                    })
            except:
                continue
        
        return {
            "total_balance": total_balance,
            "accounts": accounts_summary,
            "count": len(accounts_summary)
        }
    
    # Yardımcı metodlar
    def _hash_token(self, token: str) -> str:
        """
        Token'ı şifreler.
        """
        return hashlib.sha256(token.encode()).hexdigest()
    
    def _guess_category(self, description: str) -> str:
        """
        İşlem açıklamasına göre kategori tahmin eder.
        """
        description_lower = description.lower()
        
        # Kategori anahtar kelimeleri
        categories = {
            "Gıda": ["market", "migros", "a101", "şok", "carrefour", "bim"],
            "Ulaşım": ["akaryakıt", "benzin", "taksi", "otobüs", "metro"],
            "Kira": ["kira", "emlak"],
            "Fatura": ["elektrik", "su", "doğalgaz", "internet", "telefon"],
            "Maaş": ["maaş", "ücret", "ödeme"]
        }
        
        for category, keywords in categories.items():
            for keyword in keywords:
                if keyword in description_lower:
                    return category
        
        return "Diğer"
    
    def _simulate_bank_api_call(self, account: BankAccount, days_back: int) -> List[Dict]:
        """
        Banka API çağrısı simülasyonu.
        Gerçek uygulamada bu, gerçek bir API çağrısı olacak.
        """
        # Gerçek bir API yerine sahte veri döndür
        transactions = []
        
        # Bugünden itibaren geriye doğru işlemler oluştur
        for i in range(days_back):
            day = datetime.now() - timedelta(days=i)
            
            # Her gün için 1-3 arası işlem oluştur
            num_transactions = (i % 3) + 1
            for j in range(num_transactions):
                # İşlem tutarı: -200 ile 1000 TL arası
                amount = ((i * j) % 12) * 100 - 200
                
                # İşlem açıklaması
                if amount > 0:
                    description = "Gelen havale" if j % 2 == 0 else "Maaş ödemesi"
                else:
                    categories = ["Market alışverişi", "Akaryakıt ödemesi", "Fatura ödemesi", "Kira ödemesi"]
                    description = categories[(i + j) % len(categories)]
                
                # İşlem oluştur
                transaction = {
                    "id": f"tx_{account.id}_{i}_{j}_{int(time.time())}",
                    "date": day.date(),
                    "amount": amount,
                    "description": description,
                    "currency": "TRY"
                }
                
                transactions.append(transaction)
        
        return transactions
    
    def _simulate_balance_api_call(self, account: BankAccount) -> Dict:
        """
        Bakiye API çağrısı simülasyonu.
        Gerçek uygulamada bu, gerçek bir API çağrısı olacak.
        """
        # Hesap ID'ye göre sabit bir bakiye oluştur
        base_balance = (account.id * 1000) % 10000
        
        return {
            "success": True,
            "account_id": account.id,
            "balance": base_balance,
            "available_balance": base_balance - 100,
            "currency": "TRY",
            "as_of": datetime.now()
        }
    
    # Önbellek metodları
    def _add_to_cache(self, key: str, data: any) -> None:
        """
        Veriyi önbelleğe ekler.
        """
        self._cache[key] = data
        self._cache_expiry[key] = time.time() + self._cache_ttl
    
    def _get_from_cache(self, key: str) -> any:
        """
        Veriyi önbellekten alır.
        """
        return self._cache.get(key)
    
    def _is_cached(self, key: str) -> bool:
        """
        Verinin önbellekte olup olmadığını ve geçerli olup olmadığını kontrol eder.
        """
        if key not in self._cache:
            return False
        
        if time.time() > self._cache_expiry.get(key, 0):
            # Süresi dolmuş, önbellekten kaldır
            self._clear_cache(key)
            return False
        
        return True
    
    def _clear_cache(self, key: str = None) -> None:
        """
        Önbelleği temizler.
        """
        if key:
            if key in self._cache:
                del self._cache[key]
            if key in self._cache_expiry:
                del self._cache_expiry[key]
        else:
            self._cache = {}
            self._cache_expiry = {} 