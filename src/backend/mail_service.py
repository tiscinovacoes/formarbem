import os

class MailService:
    @staticmethod
    def send_welcome_email(user_email, course_name):
        # Em produção, usar bibliotecas como SMTPLib ou serviços como SendGrid/AWS SES
        print(f"--- SIMULANDO ENVIO DE E-MAIL ---")
        print(f"Para: {user_email}")
        print(f"Assunto: Bem-vindo ao {course_name} | Instituto Formar Bem")
        print(f"Mensagem: Sua matrícula foi confirmada. Acesse sua área do aluno em https://formarbem.org.br/aluno")
        print(f"-------------------------------")
        return True
