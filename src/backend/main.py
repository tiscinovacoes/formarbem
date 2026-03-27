from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from providers.mercadopago import MercadoPagoProvider
import os
import json
from dotenv import load_dotenv

load_dotenv()

app = FastAPI()

# Enable CORS for the static site to call the API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this to your domain
    allow_methods=["*"],
    allow_headers=["*"],
)

from mail_service import MailService

MP_ACCESS_TOKEN = os.getenv("MP_ACCESS_TOKEN")
payment_manager = MercadoPagoProvider(MP_ACCESS_TOKEN)
mail_service = MailService()

@app.get("/checkout/{course_id}")
async def create_checkout(course_id: str):
    # Load course data from JSON instead of mocking here
    courses_path = os.path.join(os.path.dirname(__file__), "../generator/content/cursos.json")
    with open(courses_path, 'r', encoding='utf-8') as f:
        courses = {c['id']: c for c in json.load(f)}
    
    course = courses.get(course_id)
    if not course:
        raise HTTPException(status_code=404, detail="Curso não encontrado")
    
    try:
        url = payment_manager.create_checkout_url(course_id, course["title"], course["price"])
        return {"checkout_url": url}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/webhooks/mercadopago")
async def mp_webhook(request: Request):
    data = await request.json()
    status = payment_manager.handle_webhook(data)
    if status == "approved":
        # logic to grant access to the user
        course_id = data.get("external_reference", "gestao") # external_reference should store course_id
        user_email = "aluno@exemplo.com" # Em produção, pegar dos dados do pagador
        mail_service.send_welcome_email(user_email, course_id)
        print(f"Pagamento aprovado e e-mail enviado para: {user_email}")
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
