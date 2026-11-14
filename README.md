# Calculadora de Lajes Maciças de Concreto Armado

Aplicação desktop em Python (PySide6) para dimensionar lajes maciças retangulares de concreto armado, **armadas em duas direções (bidirecionais) ou em uma direção (unidirecionais)**, conforme Carvalho & Figueiredo, Bastos e as normas ABNT NBR 6118 e NBR 6120.

Este guia explica como rodar o projeto localmente e como gerar o executável e o instalador para Windows.

---

## Como a aplicação funciona

1. **Geometria:** informe os dois vãos. O menor é tratado como `lx` e o maior como `ly`. A laje é classificada automaticamente pela relação λ = ly/lx:
   - λ ≤ 2: **bidirecional**, casos de vinculação 1 a 9;
   - λ > 2: **unidirecional**, faixa de 1 m no menor vão (A-A, E-A ou E-E).
2. **Vinculação:** escolha pelo menu ou clicando no diagrama correspondente.
3. **Parâmetros:** classe de agressividade (CAA), bitola φ, carga variável qk e espessura h (em cm). As demais hipóteses (cargas permanentes, aço CA-50, fck mínimo da CAA etc.) são fixas e exibidas na tela.
4. **Resultados:** momentos, reações, armaduras, flechas, parecer final e memória de cálculo completa, com exportação em PDF.

---

## Pré-requisitos

- **Python 3.10 ou superior** (no Windows, marque *Add Python to PATH* na instalação)
- **Git**
- **Inno Setup 6** (só para gerar o instalador): https://jrsoftware.org/isdl.php

---

## 1. Clonar o repositório

```bash
git clone https://github.com/SEU-USUARIO/SlabCalc.git
cd SlabCalc
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

Versão de terminal (opcional, sem interface gráfica):

```bash
python cli.py
```

## 5. Testar (opcional)

O script `test_paridade.py` compara o fluxo da interface com o fluxo original de terminal em 14 casos (bidirecionais casos 1 a 9, unidirecionais A-A, E-A e E-E, e combinações extras de CAA, bitola, carga e espessura). Ele compara os dados de entrada e a memória de cálculo completa:

```bash
python test_paridade.py
```

O resultado esperado termina com `Todos os casos idênticos.`

---

## 6. Gerar o executável

Com o ambiente virtual ativo, na raiz do projeto:

```bash
pyinstaller --noconfirm --windowed --name SlabCalc --icon assets\ico.ico --add-data "assets;assets" main.py
```

- `--icon` define o ícone do arquivo `.exe`.
- `--add-data "assets;assets"` embute a pasta `assets` no pacote, necessária para o ícone da janela aparecer. No Linux/macOS use `:` no lugar de `;`.

Para refazer o build do zero (por exemplo, ao trocar o ícone), apague os arquivos anteriores antes:

```bash
rmdir /s /q build
rmdir /s /q dist
del SlabCalc.spec
```

O resultado fica em:

```
dist\SlabCalc\SlabCalc.exe
```

Para distribuir, use a pasta `dist\SlabCalc` **inteira** (o `.exe` depende da pasta `_internal` e das DLLs). O arquivo em `build\SlabCalc\` é apenas intermediário, não use.

> Os avisos `update_exe_pe_checksum ... OSError(22)` no log do PyInstaller são inofensivos. O build terminou com sucesso quando aparece `Build complete!`.

---

## 7. Gerar o instalador (Windows)

1. Instale o **Inno Setup 6**.
2. Confirme que o arquivo `instalador.iss` está na raiz do projeto, ao lado da pasta `dist`.
3. Se for uma versão nova, atualize o número da versão no `instalador.iss` (por exemplo, `2.0.0`).
4. Abra o `instalador.iss` no **Inno Setup Compiler**.
5. Compile com `Ctrl+F9` (ou **Build -> Compile**).

O instalador é gerado em:

```
instalador\SlabCalc-Setup-2.0.0.exe
```

A compressão pode levar alguns minutos, porque o PySide6 é grande.

---

## 8. Publicar uma versão (opcional)

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
4. Crie a tag (ex.: `v2.0.0`), anexe o `SlabCalc-Setup-2.0.0.exe` e clique em **Publish release**.

---

## Problemas comuns

| Problema | Solução |
|---|---|
| `ModuleNotFoundError: No module named 'PySide6'` | O ambiente virtual não está ativo. Ative-o (passo 2) e instale as dependências (passo 3). |
| `ModuleNotFoundError: No module named 'calculo'` | Rode os comandos a partir da raiz do projeto, onde estão `calculo.py` e `gui.py`. |
| `'source' não é reconhecido` | `source` só existe em Bash. No CMD use `.venv\Scripts\activate`. |
| `Icon input file ... not found` | O arquivo `assets\ico.ico` não existe. Crie-o ou rode o build sem `--icon`. |
| Ícone do `.exe` aparece, mas o da janela não | Faltou `--add-data "assets;assets"` no build. Refaça o build com o comando completo do passo 6. |
| Ícone antigo continua aparecendo | Cache de ícones do Windows. Copie o `.exe` para outra pasta ou reinicie o Explorer. |
| Texto cortado nos quadros da primeira aba | Use a versão atual do `gui.py`: a coluna esquerda tem rolagem e quadros de altura fixa. |
| `QFont::setPointSize: Point size <= 0` | Aviso inofensivo. Para removê-lo, use `QFont("Consolas", 10)` na área de saída. |
| SmartScreen bloqueia o instalador | O executável não é assinado. Clique em **Mais informações → Executar assim mesmo**. |
| Antivírus acusa falso positivo | Comum em executáveis do PyInstaller. Mantenha o modo pasta (*onedir*), não `--onefile`. |

---

## Estrutura do projeto

```
SlabCalc/
├── main.py              # ponto de entrada da interface
├── calculo.py           # tabelas, fórmulas e funções de cálculo
├── gui.py               # interface PySide6
├── cli.py               # versão de terminal (opcional)
├── test_paridade.py     # teste: interface x fluxo original de terminal
├── instalador.iss       # script do Inno Setup
├── requirements.txt
├── .gitignore
└── assets/
    └── ico.ico          # ícone da aplicação
```

---

## Aviso

Ferramenta de apoio acadêmico, com escopo limitado: lajes maciças retangulares, bidirecionais (casos 1 a 9) e unidirecionais (faixa de 1 m nos casos A-A, E-A e E-E), com as hipóteses fixas exibidas na interface. Os resultados devem ser conferidos por um engenheiro responsável antes de qualquer uso em projeto real.