import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging
import os

class EmailService:
    """E-posta gönderimi için servis sınıfı."""
    
    def __init__(self, smtp_server=None, smtp_port=None, smtp_user=None, smtp_password=None):
        """
        EmailService sınıfı için yapıcı metod.
        
        Args:
            smtp_server: SMTP sunucu adresi (varsayılan: çevresel değişken veya None)
            smtp_port: SMTP port numarası (varsayılan: çevresel değişken veya 587)
            smtp_user: SMTP kullanıcı adı/e-posta (varsayılan: çevresel değişken veya None)
            smtp_password: SMTP şifresi (varsayılan: çevresel değişken veya None)
        """
        # Çevresel değişkenlerden veya parametrelerden SMTP ayarlarını al
        self.smtp_server = smtp_server or os.environ.get('SMTP_SERVER')
        self.smtp_port = smtp_port or os.environ.get('SMTP_PORT', 587)
        self.smtp_user = smtp_user or os.environ.get('SMTP_USER')
        self.smtp_password = smtp_password or os.environ.get('SMTP_PASSWORD')
        
        # Loglama için
        self.logger = logging.getLogger(__name__)
        
    def is_configured(self):
        """SMTP ayarlarının yapılandırılıp yapılandırılmadığını kontrol eder."""
        return all([self.smtp_server, self.smtp_port, self.smtp_user, self.smtp_password])
    
    def send_email(self, to_email, subject, body, is_html=False):
        """
        E-posta gönderir.
        
        Args:
            to_email: Alıcı e-posta adresi
            subject: E-posta konusu
            body: E-posta içeriği
            is_html: İçeriğin HTML olup olmadığı (varsayılan: False)
            
        Returns:
            bool: E-posta gönderimi başarılı ise True, aksi halde False
        """
        if not self.is_configured():
            self.logger.error("SMTP ayarları yapılandırılmamış!")
            return False
            
        if not to_email:
            self.logger.error("Alıcı e-posta adresi belirtilmemiş!")
            return False
            
        try:
            # E-posta mesajı oluştur
            msg = MIMEMultipart()
            msg['From'] = self.smtp_user
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # İçerik türüne göre ekle
            if is_html:
                msg.attach(MIMEText(body, 'html'))
            else:
                msg.attach(MIMEText(body, 'plain'))
                
            # SMTP sunucusuna bağlan
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()  # TLS güvenlik bağlantısını başlat
            server.login(self.smtp_user, self.smtp_password)
            
            # E-postayı gönder
            server.send_message(msg)
            server.quit()
            
            self.logger.info(f"E-posta başarıyla gönderildi: {to_email}")
            return True
            
        except Exception as e:
            self.logger.error(f"E-posta gönderilirken hata oluştu: {str(e)}")
            return False
            
    def send_notification_email(self, user, notification):
        """
        Bildirim e-postası gönderir.
        
        Args:
            user: Kullanıcı nesnesi
            notification: Bildirim nesnesi
            
        Returns:
            bool: E-posta gönderimi başarılı ise True, aksi halde False
        """
        # Kullanıcının bildirim tercihlerini kontrol et
        user_prefs = user.get_notification_preferences()
        
        # E-posta bildirimleri kapalıysa gönderme
        if not user_prefs.get("email_notifications", True):
            return False
            
        # Bildirim tipi için tercih kontrol et
        notification_type = notification.type.value
        if not user_prefs.get("notification_types", {}).get(notification_type, True):
            return False
            
        # E-posta içeriğini hazırla
        subject = f"Kişisel Finans Bildirimi: {notification.title}"
        
        # HTML formatında e-posta içeriği
        html_content = f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background-color: #3498db; color: white; padding: 10px 20px; border-radius: 5px 5px 0 0; }}
                .content {{ background-color: #f9f9f9; padding: 20px; border-radius: 0 0 5px 5px; }}
                .notification {{ border-left: 4px solid #3498db; padding: 10px; margin: 10px 0; background-color: white; }}
                .footer {{ font-size: 12px; text-align: center; margin-top: 20px; color: #888; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h2>Kişisel Finans</h2>
                </div>
                <div class="content">
                    <h3>Merhaba {user.username},</h3>
                    <p>Aşağıdaki bildiriminiz var:</p>
                    
                    <div class="notification">
                        <h4>{notification.title}</h4>
                        <p>{notification.message}</p>
                        <small>Tarih: {notification.created_at.strftime('%d.%m.%Y %H:%M')}</small>
                    </div>
                    
                    <p>Uygulamayı açarak daha fazla bilgi edinebilirsiniz.</p>
                </div>
                <div class="footer">
                    <p>Bu e-posta Kişisel Finans uygulaması tarafından otomatik olarak gönderilmiştir.</p>
                    <p>Bildirim tercihlerinizi değiştirmek için uygulama içindeki Ayarlar sayfasını ziyaret edebilirsiniz.</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        # E-postayı gönder
        return self.send_email(user.email, subject, html_content, is_html=True) 