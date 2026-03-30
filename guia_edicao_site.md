# 📖 Guia de Edição do Site — Instituto Formar Bem

## Como funciona o site

O site é gerado a partir de **arquivos de conteúdo simples** (`.md` e `.json`) que você edita, e depois um script monta o HTML final e publica automaticamente via GitHub → Vercel.

---

## 🗂️ Estrutura dos arquivos de conteúdo

Todos os textos editáveis ficam em:
```
formarbem/
└── src/
    └── generator/
        └── content/          ← AQUI você edita os textos
            ├── index.md      ← Página inicial (Home)
            ├── cursos.md     ← Página de cursos
            ├── cursos.json   ← Dados dos cursos (nome, preço, etc.)
            ├── orcamentos.md ← Página de orçamentos
            ├── aluno.md      ← Área do aluno
            ├── sucesso.md    ← Página de pagamento aprovado
            └── erro.md       ← Página de erro no pagamento
```

---

## ✏️ Como editar textos

### Passo 1 — Abra o arquivo no VS Code
Abra o VS Code na pasta do projeto e navegue até `src/generator/content/`.

### Passo 2 — Edite o arquivo `.md` da página desejada

Os arquivos usam **Markdown** com um cabeçalho (`---`) de configuração:

```markdown
---
title: Meu Título
---

Aqui vai o texto da página em Markdown normal.

## Seção 1
Parágrafo de texto...
```

**Exemplo — mudar o título da página inicial:**
Abra `content/index.md` e edite o campo `title:` no topo.

---

## 🎓 Como editar os cursos

Abra o arquivo `src/generator/content/cursos.json`:

```json
[
  {
    "id": "gestao",
    "nome": "Gestão Escolar",
    "descricao": "Descrição do curso...",
    "preco": 297.00,
    "duracao": "40 horas"
  }
]
```

Para **adicionar um curso novo**, copie um bloco e cole logo abaixo, separado por vírgula. Altere o `"id"` para algo único (sem espaços, sem acentos).

> ⚠️ O campo `"id"` deve coincidir com o que é passado para o checkout de pagamento.

---

## 🖼️ Como trocar imagens

As imagens ficam em `src/generator/static/` (ou referenciadas no HTML).

1. Coloque o novo arquivo de imagem na pasta `static/`
2. Edite o template HTML correspondente em `src/generator/templates/` para apontar para o novo arquivo

---

## 🚀 Como publicar as alterações

Após editar qualquer arquivo, siga esses passos no terminal (PowerShell):

```powershell
# 1. Entrar na pasta do projeto
cd C:\Users\lucareis\.gemini\formarbem

# 2. Regenerar o site (converter .md → .html)
python src/generator/main.py

# 3. Enviar para o GitHub (isso publica no Vercel automaticamente)
git add .
git commit -m "atualização: descreva o que mudou"
git push origin main
```

O **Vercel detecta o push automaticamente** e publica em ~1 minuto em `formarbem.com`.

---

## 📋 Resumo rápido

| O que quero fazer | Onde editar |
|---|---|
| Mudar textos da Home | `src/generator/content/index.md` |
| Mudar textos de Cursos | `src/generator/content/cursos.md` |
| Adicionar/editar cursos | `src/generator/content/cursos.json` |
| Mudar textos de Orçamentos | `src/generator/content/orcamentos.md` |
| Mudar página de sucesso | `src/generator/content/sucesso.md` |
| Trocar imagens | `src/generator/static/` |
| Mudar layout/design | `src/generator/templates/*.html` |

---

## 🔑 Variáveis de ambiente (senhas e tokens)

Nunca coloque senhas no código. As configurações sensíveis ficam no Railway:
- `MP_ACCESS_TOKEN` — Token do Mercado Pago
- `BASE_URL` — URL do site (`https://formarbem.com`)

Para alterar, acesse [railway.app](https://railway.app) → seu projeto → **Variables**.

---

## ❓ Problemas comuns

**O site não atualizou depois do push:**
→ Verifique o painel do Vercel em [vercel.com](https://vercel.com) — o deploy deve aparecer em andamento.

**Erro ao rodar o gerador:**
→ Certifique-se que o Python está instalado. Rode `python --version` no terminal.

**Curso não aparece no checkout:**
→ Confirme que o campo `"id"` no `cursos.json` é exatamente igual ao usado no botão HTML.
