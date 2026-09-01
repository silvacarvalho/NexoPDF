# Nexo PDF

Aplicativo Web para combinar PDFs e imagens em um único PDF ou dividir PDFs de forma simples e prática.
- **Combinar** vários PDFs e/ou imagens (JPG, PNG, WEBP...) em um único arquivo PDF, reordenando por arrastar-e-soltar. Cada imagem vira uma página no mesmo formato/proporção da imagem original.
- **Dividir** um PDF arrastando miniaturas das páginas para uma caixa de seleção (mais intervalo de páginas, divisão em lote e intervalos personalizados nas opções avançadas).

O resultado sempre pode ser baixado diretamente pelo navegador (PDF único ou `.zip` com várias partes).

> Nexo PDF nasceu como uma ferramenta de combinar/dividir PDFs, mas a ideia é crescer como um conjunto de utilitários de PDF (compressão, conversão, marca d'água, assinatura, etc.).

## Rodar localmente

```bash
pip install -r requirements.txt
streamlit run app.py
```

O navegador abre automaticamente em `http://localhost:8501`.

## Publicar na web (Streamlit Community Cloud — grátis)

1. Suba esta pasta para um repositório no GitHub (inclua `app.py`, `components/` e `requirements.txt`).
2. Acesse [share.streamlit.io](https://share.streamlit.io), faça login com sua conta GitHub.
3. Clique em **New app**, selecione o repositório, branch e o arquivo `app.py`.
4. Clique em **Deploy**. Em poucos minutos o app fica disponível numa URL pública.

Qualquer alteração enviada (`git push`) para o repositório atualiza o app publicado automaticamente.

### Alternativas de deploy
- **Docker + qualquer VPS/Cloud Run/Azure App Service**: crie um `Dockerfile` simples com `CMD ["streamlit", "run", "app.py", "--server.port=8080", "--server.address=0.0.0.0"]`.
- **Hugging Face Spaces**: também suporta Streamlit nativamente, processo parecido ao Streamlit Cloud.

## Estrutura

```
combinar_pdf/
├── app.py                          # aplicativo Streamlit (interface + lógica)
├── requirements.txt                # dependências (streamlit, pypdf, pymupdf)
├── components/                     # componentes Streamlit próprios (HTML/JS, sem build step)
│   ├── reorder_list/                 # lista arrastável (aba Combinar)
│   └── page_picker/                  # miniaturas + caixa de seleção (aba Dividir)
└── README.md
```
