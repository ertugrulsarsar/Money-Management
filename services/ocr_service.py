import os
import re
import cv2
import numpy as np
import pytesseract
from PIL import Image
from datetime import datetime
from sqlalchemy.orm import Session
from models.database import Transaction, Receipt
from typing import Dict, List, Optional, Tuple, Union

class OCRService:
    def __init__(self, db: Session, tesseract_path: Optional[str] = None):
        """
        OCR servisini başlatır.
        
        Args:
            db: Veritabanı oturumu
            tesseract_path: Tesseract OCR binary'sinin yolu (Windows için gerekli)
        """
        self.db = db
        
        # Tesseract yolunu belirle
        if tesseract_path:
            pytesseract.pytesseract.tesseract_cmd = tesseract_path
        elif os.environ.get("TESSERACT_PATH"):
            pytesseract.pytesseract.tesseract_cmd = os.environ.get("TESSERACT_PATH")
        
        # Kategori kelimeleri - gelişmiş karşılık tablosu
        self.category_keywords = {
            "Gıda": ["market", "migros", "a101", "şok", "carrefour", "bim", "makarna", "pirinç", "ekmek", 
                     "sebze", "meyve", "süt", "yoğurt", "peynir", "et", "tavuk", "balık", "bakkal", "manav"],
            "Sağlık": ["eczane", "hastane", "ilaç", "muayene", "doktor", "vitamin", "bandaj", "sağlık"],
            "Ulaşım": ["akaryakıt", "benzin", "dizel", "lpg", "otobüs", "metro", "taksi", "bilet", "opet", 
                       "shell", "bp", "petrol", "otopark", "ulaşım", "yol", "tren", "uçak"],
            "Eğlence": ["sinema", "tiyatro", "konser", "festival", "müze", "park", "eğlence", "oyun"],
            "Giyim": ["mağaza", "lcw", "defacto", "h&m", "zara", "giyim", "ayakkabı", "çanta", "takı", "aksesuar"],
            "Elektronik": ["teknoloji", "telefon", "bilgisayar", "tablet", "kulaklık", "şarj", "vatan", 
                          "mediamarkt", "teknosa", "elektronik"],
            "Kira": ["kira", "konut", "emlak", "apartman"],
            "Fatura": ["elektrik", "su", "doğalgaz", "internet", "telefon", "fatura", "ödeme"]
        }
    
    def process_receipt_image(self, image_data: Union[str, bytes, np.ndarray]) -> Dict:
        """
        Makbuz görüntüsünü işler ve bilgileri çıkarır.
        
        Args:
            image_data: Görüntü verisi (dosya yolu, bytes veya numpy array)
            
        Returns:
            Çıkarılan bilgileri içeren sözlük
        """
        # Görüntüyü yükle
        if isinstance(image_data, str):  # Dosya yolu
            image = cv2.imread(image_data)
        elif isinstance(image_data, bytes):  # Bytes
            nparr = np.frombuffer(image_data, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        else:  # Numpy array
            image = image_data
        
        # Görüntü ön işleme
        processed_image = self._preprocess_image(image)
        
        # OCR ile metni çıkar
        text = pytesseract.image_to_string(processed_image, lang='tur')
        
        # Bilgileri çıkar
        amount = self._extract_amount(text)
        date = self._extract_date(text)
        category = self._extract_category(text)
        
        return {
            "text": text,
            "amount": amount,
            "date": date,
            "category": category
        }
    
    def save_receipt(self, user_id: int, image_data: bytes, receipt_info: Dict) -> Receipt:
        """
        Makbuz bilgilerini veritabanına kaydeder.
        
        Args:
            user_id: Kullanıcı ID'si
            image_data: Makbuz görüntüsü (bytes)
            receipt_info: Makbuz bilgileri
            
        Returns:
            Kaydedilen makbuz nesnesi
        """
        # Makbuzu kaydet
        receipt = Receipt(
            user_id=user_id,
            image=image_data,
            ocr_text=receipt_info["text"],
            amount=receipt_info["amount"],
            date=receipt_info["date"],
            category=receipt_info["category"]
        )
        
        self.db.add(receipt)
        self.db.commit()
        self.db.refresh(receipt)
        
        # İşlem oluştur
        transaction = Transaction(
            user_id=user_id,
            amount=receipt_info["amount"],
            type="expense",
            category=receipt_info["category"],
            description=f"OCR ile eklendi - Makbuz #{receipt.id}",
            date=receipt_info["date"] or datetime.now().date()
        )
        
        self.db.add(transaction)
        self.db.commit()
        
        return receipt
    
    def get_user_receipts(self, user_id: int, page: int = 1, per_page: int = 10) -> Dict:
        """
        Kullanıcıya ait makbuzları getirir.
        
        Args:
            user_id: Kullanıcı ID'si
            page: Sayfa numarası
            per_page: Sayfa başına makbuz sayısı
            
        Returns:
            Makbuzları içeren sözlük
        """
        # Toplam makbuz sayısı
        total_receipts = self.db.query(Receipt).filter(Receipt.user_id == user_id).count()
        
        # Toplam sayfa sayısı
        total_pages = (total_receipts + per_page - 1) // per_page
        
        # Makbuzları getir
        receipts = self.db.query(Receipt).filter(
            Receipt.user_id == user_id
        ).order_by(
            Receipt.date.desc()
        ).offset(
            (page - 1) * per_page
        ).limit(per_page).all()
        
        return {
            "receipts": receipts,
            "total": total_receipts,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages
        }
    
    def _preprocess_image(self, image: np.ndarray) -> Image.Image:
        """
        OCR için görüntüye ön işleme uygular.
        
        Args:
            image: İşlenecek görüntü
            
        Returns:
            İşlenmiş görüntü
        """
        # Gri tonlamaya dönüştür
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Gürültü azaltma
        denoised = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Binarizasyon
        _, binary = cv2.threshold(denoised, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
        
        # PIL formatına dönüştür
        pil_image = Image.fromarray(binary)
        
        return pil_image
    
    def _extract_amount(self, text: str) -> Optional[float]:
        """
        Metinden tutarı çıkarır.
        
        Args:
            text: OCR ile çıkarılan metin
            
        Returns:
            Tutar (varsa)
        """
        # Farklı tutar formatları için regex
        patterns = [
            r'(?:TOPLAM|TUTAR|FİYAT|Toplam|Tutar)\s*:?\s*(?:TL)?[₺₤]?\s*([0-9]+[.,][0-9]+)',  # TOPLAM: 123,45
            r'(?:TOPLAM|TUTAR|FİYAT|Toplam|Tutar)\s*:?\s*(?:TL)?[₺₤]?\s*([0-9]+)',  # TOPLAM: 123
            r'([0-9]+[.,][0-9]+)\s*(?:TL|₺|₤)',  # 123,45 TL
            r'(?:TL|₺|₤)\s*([0-9]+[.,][0-9]+)',  # TL 123,45
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                # İlk bulunan tutarı al
                amount_str = matches[0].replace(',', '.') if ',' in matches[0] else matches[0]
                try:
                    return float(amount_str)
                except ValueError:
                    continue
        
        return None
    
    def _extract_date(self, text: str) -> Optional[datetime.date]:
        """
        Metinden tarihi çıkarır.
        
        Args:
            text: OCR ile çıkarılan metin
            
        Returns:
            Tarih (varsa)
        """
        # Farklı tarih formatları için regex
        patterns = [
            r'(\d{2})[./](\d{2})[./](\d{4})',  # 31/12/2023 veya 31.12.2023
            r'(\d{2})-(\d{2})-(\d{4})',  # 31-12-2023
            r'(\d{4})[./](\d{2})[./](\d{2})'  # 2023/12/31 veya 2023.12.31
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text)
            if matches:
                # İlk bulunan tarihi al
                date_parts = matches[0]
                try:
                    if len(date_parts[0]) == 4:  # yyyy/mm/dd
                        year, month, day = date_parts
                    else:  # dd/mm/yyyy
                        day, month, year = date_parts
                    
                    return datetime(int(year), int(month), int(day)).date()
                except (ValueError, IndexError):
                    continue
        
        return None
    
    def _extract_category(self, text: str) -> str:
        """
        Metinden kategoriyi tahmin eder.
        
        Args:
            text: OCR ile çıkarılan metin
            
        Returns:
            Kategori
        """
        text_lower = text.lower()
        
        # Kategori eşleşme sayıları
        category_matches = {category: 0 for category in self.category_keywords}
        
        # Her kategori için anahtar kelimeleri ara
        for category, keywords in self.category_keywords.items():
            for keyword in keywords:
                if keyword.lower() in text_lower:
                    category_matches[category] += 1
        
        # En çok eşleşen kategoriyi bul
        best_category = max(category_matches.items(), key=lambda x: x[1])
        
        # Eşleşme yoksa "Diğer" döndür
        if best_category[1] == 0:
            return "Diğer"
        
        return best_category[0] 