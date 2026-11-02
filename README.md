# Calculadora de Lajes Maciças de Concreto Armado

Aplicação desktop em Python (PySide6) para dimensionar lajes maciças retangulares de concreto armado, armadas em duas direções, conforme Carvalho & Figueiredo e a ABNT NBR 6118.

Este guia explica como rodar o projeto localmente e como gerar o executável e o instalador para Windows.

---

## Pré-requisitos

- **Python 3.10 ou superior** (no Windows, marque *Add Python to PATH* na instalação)
- **Git**
- **Inno Setup 6** (só para gerar o instalador): https://jrsoftware.org/isdl.php

---

## 1. Clonar o repositório

```bash
git clone https://github.com/SEU-USUARIO/Calculo-de-lajes.git
cd Calculo-de-lajes
```

## 2. Criar e ativar o ambiente virtual

```bash
python -m venv .venv
```

Ative conforme o seu terminal:

| Terminal | Comando |
|---|---|
| CMD (Windows) | `.venv\Scripts\activate` |
| PowerShell | `.venv\Scripts\Activate.ps1` |
| Git Bash | `source .venv/Scripts/activate` |
| Linux / macOS | `source .venv/bin/activate` |

Quando estiver ativo, o terminal mostra `(.venv)` no início da linha.

> No PowerShell, se aparecer erro de política de execução, rode uma vez:
> `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned`

## 3. Instalar as dependências

```bash
pip install -r requirements.txt
```

Se o arquivo não existir, instale direto:

```bash
pip install PySide6-Essentials pyinstaller
```

## 4. Rodar o projeto

```bash
python main.py
```

Sem ativar o ambiente, também funciona:

```bash
.venv\Scripts\python main.py
```

---

## 5. Gerar o executável

Com o ambiente virtual ativo, na raiz do projeto:

```bash
pyinstaller --noconfirm --windowed --name CalculoLajes --icon assets\ico.ico main.py
```

Para refazer o build do zero (por exemplo, ao trocar o ícone), apague os arquivos anteriores antes:

```bash
rmdir /s /q build
rmdir /s /q dist
del CalculoLajes.spec
```

O resultado fica em:

```
dist\CalculoLajes\CalculoLajes.exe
```

Para distribuir, use a pasta `dist\CalculoLajes` **inteira** (o `.exe` depende da pasta `_internal` e das DLLs).

> Os avisos `update_exe_pe_checksum ... OSError(22)` no log do PyInstaller são inofensivos. O build terminou com sucesso quando aparece `Build complete!`.

---

## 6. Gerar o instalador (Windows)

1. Instale o **Inno Setup 6**.
2. Confirme que o arquivo `instalador.iss` está na raiz do projeto, ao lado da pasta `dist`.
3. Abra o `instalador.iss` no **Inno Setup Compiler**.
4. Compile com `Ctrl+F9` (ou **Build → Compile**).

O instalador é gerado em:

```
instalador\CalculoLajes-Setup-1.0.0.exe
```

A compressão pode levar alguns minutos, porque o PySide6 é grande.

---

## 7. Publicar uma versão (opcional)

1. Garanta que o `.gitignore` contenha:

   ```
   __pycache__/
   .venv/
   build/
   dist/
   instalador/
   *.spec
   ```

2. Faça commit e push do código.
3. No GitHub, vá em **Releases → Draft a new release**.
4. Crie a tag (ex.: `v1.0.0`), anexe o `CalculoLajes-Setup-1.0.0.exe` e clique em **Publish release**.

---

## Problemas comuns

| Problema | Solução |
|---|---|
| `ModuleNotFoundError: No module named 'PySide6'` | O ambiente virtual não está ativo. Ative-o (passo 2) e instale as dependências (passo 3). |
| `'source' não é reconhecido` | `source` só existe em Bash. No CMD use `.venv\Scripts\activate`. |
| `Icon input file ... not found` | O arquivo `assets\ico.ico` não existe. Crie-o ou rode o build sem `--icon`. |
| Ícone antigo continua aparecendo | Cache de ícones do Windows. Copie o `.exe` para outra pasta ou reinicie o Explorer. |
| `QFont::setPointSize: Point size <= 0` | Aviso inofensivo. Para removê-lo, use `QFont("Consolas", 10)` na área de saída. |
| SmartScreen bloqueia o instalador | O executável não é assinado. Clique em **Mais informações → Executar assim mesmo**. |
| Antivírus acusa falso positivo | Comum em executáveis do PyInstaller. Mantenha o modo pasta (*onedir*), não `--onefile`. |

---

## Estrutura do projeto

```
Calculo-de-lajes/
├── main.py              # ponto de entrada
├── calculo.py           # tabelas e funções de cálculo
├── gui.py               # interface PySide6
├── instalador.iss       # script do Inno Setup
├── requirements.txt
├── .gitignore
└── assets/
    └── ico.ico          # ícone da aplicação
```

---

## Aviso

Ferramenta de apoio acadêmico, com escopo limitado (lajes armadas em duas direções, casos 1 a 6, fck de 20 a 40 MPa). Os resultados devem ser conferidos por um engenheiro responsável antes de qualquer uso em projeto real.