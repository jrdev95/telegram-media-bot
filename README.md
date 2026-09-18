# Telegram Media Bot

Bot do Telegram que responde a links do **Instagram**, **TikTok**, **Threads**, **X (Twitter)**, **YouTube Shorts**, **Reddit** e **Erome** enviados no chat/grupo com a mídia baixada (foto, vídeo ou álbum, quando houver mais de uma).

## Como funciona

- O bot fica "ouvindo" mensagens que contenham um link de uma das plataformas suportadas.
- Baixa a mídia (com `yt-dlp` e, quando necessário, métodos alternativos por plataforma).
- Responde a mensagem original com a mídia — **sem legenda**.
- Se houver mais de uma mídia no post, envia como álbum.
- Processa apenas links enviados enquanto o bot está rodando; mensagens recebidas enquanto ele estava desligado são ignoradas quando ele volta a ficar online.
- Se o download falhar, o bot simplesmente não responde (nenhum erro técnico é mostrado no chat).

## Pré-requisitos

- Python 3.9 ou superior
- `ffmpeg` instalado no sistema (necessário para o `yt-dlp` juntar áudio e vídeo em alguns casos)
- Um token de bot do Telegram, criado com o [@BotFather](https://t.me/BotFather)

---

## Instalação no Linux

1. **Instale o Python e o ffmpeg** (caso ainda não tenha):
   ```bash
   sudo apt update
   sudo apt install python3 python3-pip python3-venv ffmpeg -y
   ```

2. **Baixe/copie os arquivos do projeto** para uma pasta, por exemplo `telegram-media-bot`, e entre nela:
   ```bash
   cd telegram-media-bot
   ```

   Dentro dessa pasta, crie uma subpasta chamada **`downloaders`** e copie para dentro dela estes arquivos: `common.py`, `instagram.py`, `tiktok.py`, `twitter.py`, `threads.py`, `youtube.py`, `reddit.py` e `erome.py`. A estrutura final precisa ficar assim:
   ```
   telegram-media-bot/
   ├── main.py
   ├── config.py
   ├── requirements.txt
   ├── .env.example
   └── downloaders/
       ├── __init__.py
       ├── common.py
       ├── instagram.py
       ├── tiktok.py
       ├── twitter.py
       ├── threads.py
       ├── youtube.py
       ├── reddit.py
       └── erome.py
   ```
   Se a pasta `downloaders` não existir no mesmo nível do `main.py`, ou se faltar algum desses arquivos dentro dela (o `__init__.py` é um arquivo vazio, então é fácil esquecê-lo ao copiar), o bot não vai iniciar e vai mostrar o erro `ModuleNotFoundError: No module named 'downloaders'`.

3. **Crie e ative um ambiente virtual** (recomendado):
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```

4. **Instale as dependências**:
   ```bash
   pip install -r requirements.txt
   ```

5. **Configure o token do bot**:
   ```bash
   cp .env.example .env
   ```
   Abra o arquivo `.env` e coloque o token gerado pelo @BotFather:
   ```
   BOT_TOKEN=123456789:AAExemploDoSeuTokenAqui
   ```

6. **Rode o bot**:
   ```bash
   python3 main.py
   ```

Para deixar rodando em segundo plano (ex: em um servidor), você pode usar `screen`, `tmux` ou configurar um serviço `systemd`.

---

## Instalação no Windows

1. **Instale o Python**:
   - Baixe em [python.org/downloads](https://www.python.org/downloads/)
   - Durante a instalação, marque a opção **"Add Python to PATH"**

2. **Instale o ffmpeg**:
   - Baixe o pacote "essentials" em [gyan.dev/ffmpeg/builds](https://www.gyan.dev/ffmpeg/builds/)
   - Extraia o `.zip` em uma pasta, por exemplo `C:\ffmpeg`
   - Adicione `C:\ffmpeg\bin` à variável de ambiente `PATH`:
     - Pesquise por "Variáveis de Ambiente" no menu Iniciar
     - Em "Variáveis do sistema", edite `Path` e adicione `C:\ffmpeg\bin`
   - Feche e abra o terminal novamente, e teste com `ffmpeg -version`

3. **Baixe/copie os arquivos do projeto** para uma pasta, por exemplo `C:\telegram-media-bot`, e abra o Prompt de Comando (ou PowerShell) nessa pasta.

   Dentro dessa pasta, crie uma subpasta chamada **`downloaders`** e copie para dentro dela estes arquivos: `common.py`, `instagram.py`, `tiktok.py`, `twitter.py`, `threads.py`, `youtube.py`, `reddit.py` e `erome.py` (veja a estrutura completa na seção do Linux acima — é a mesma nos dois sistemas). Não esqueça do `__init__.py` (arquivo vazio) dentro de `downloaders`, ou o bot vai falhar com `ModuleNotFoundError: No module named 'downloaders'`.

4. **Crie e ative um ambiente virtual**:
   ```bat
   python -m venv venv
   venv\Scripts\activate
   ```

5. **Instale as dependências**:
   ```bat
   pip install -r requirements.txt
   ```

6. **Configure o token do bot**:
   - Copie o arquivo `.env.example` e renomeie a cópia para `.env`
   - Abra o `.env` em um editor de texto e coloque o token do @BotFather:
     ```
     BOT_TOKEN=123456789:AAExemploDoSeuTokenAqui
     ```

7. **Rode o bot**:
   ```bat
   python main.py
   ```

---

## Como obter o token do bot

1. Abra uma conversa com o [@BotFather](https://t.me/BotFather) no Telegram
2. Envie `/newbot` e siga as instruções (nome e username do bot)
3. O BotFather vai te enviar um token no formato `123456789:AAExemplo...`
4. Cole esse token no arquivo `.env`, na variável `BOT_TOKEN`

## Adicionando o bot a um grupo

1. Adicione o bot ao grupo normalmente
2. Por padrão, bots do Telegram só recebem mensagens de comando em grupos. Para que o bot veja **todas** as mensagens (necessário para detectar os links), desative o "Privacy Mode":
   - Fale com o @BotFather
   - Envie `/mybots` → selecione seu bot → **Bot Settings** → **Group Privacy** → **Turn off**

## Estrutura do projeto

```
telegram-media-bot/
├── main.py
├── config.py
├── requirements.txt
├── .env.example
└── downloaders/
    ├── common.py
    ├── instagram.py
    ├── tiktok.py
    ├── twitter.py
    ├── threads.py
    ├── youtube.py
    ├── reddit.py
    └── erome.py
```

## Comportamento das mensagens

- Assim que detecta um link suportado, o bot responde com **"⏳ Fazendo o download..."**.
- Se der certo, essa mensagem é apagada e a mídia é enviada no lugar (sem legenda).
- Se falhar, a mensagem é editada para **"❌ Não foi possível baixar nenhuma mídia neste link!"** — o erro técnico nunca aparece no chat, só fica registrado no console/log.
- Mensagens recebidas enquanto o bot estava desligado são descartadas assim que ele volta a ficar online — só links enviados a partir do momento em que o bot está rodando são processados.

## Limitações conhecidas (versão de testes)

- **Threads** não tem API pública estável nem suporte oficial no `yt-dlp` — o método usado faz scraping do HTML da página do post usando um User-Agent de crawler para contornar a tela de login. Isso é inerentemente frágil e pode parar de funcionar se a Meta mudar a estrutura da página. Existe um plugin de terceiros (`yt-dlp-threads`) que cobre vídeos de forma mais robusta — veja a seção abaixo.
- **TikTok**: o extrator nativo do `yt-dlp` para TikTok anda instável (falhas conhecidas e recentes). O bot usa como fallback a API pública `tikwm.com`, que cobre vídeo único e carrossel de fotos.
- **Reddit**: galerias (`is_gallery`) são baixadas via API pública do próprio Reddit; posts de vídeo hospedados fora do Reddit (ex: links para outros sites) dependem do suporte do `yt-dlp` a esses sites.
- **Erome**: o método usado faz scraping do HTML da página do álbum; funciona tanto em `erome.com` quanto em `pt.erome.com`.
- O timeout de leitura do cliente da Bot API é de **120 segundos** — downloads que demorarem mais que isso vão falhar (silenciosamente, com a mensagem de erro padrão).
- O Telegram limita o envio de vídeo por bots comuns a **50 MB**; vídeos maiores que isso vão falhar (comportamento intencional pedido no projeto).
- Álbuns são limitados a **10 itens** (limite do próprio Telegram).
- Instagram e TikTok podem, em raras ocasiões, exigir login para certos conteúdos privados — esses casos não são suportados nesta versão.
- Todo vídeo baixado é convertido para **.mp4** (via FFmpeg, se necessário) para garantir que o player nativo do Telegram consiga tocar o arquivo.

## Melhorando o suporte a Threads (opcional)

Para tornar o download de **vídeos** do Threads mais robusto, você pode instalar o plugin `yt-dlp-threads`, que ensina o próprio `yt-dlp` a extrair vídeos da plataforma (o fallback por scraping do bot continua funcionando normalmente para fotos):

```bash
pip install git+https://github.com/tribixbite/yt-dlp-threads
```

Isso não exige nenhuma mudança no código — o `yt-dlp` passa a reconhecer links do Threads automaticamente assim que o plugin estiver instalado no mesmo ambiente virtual do bot.
