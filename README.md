# NavalForge Concept

**Plataforma aberta, modular e auditável para projeto conceitual e básico de lanchas.**

Versão pública conectada: **0.1.6**

NavalForge Concept transforma requisitos de missão em alternativas preliminares
de lanchas monocasco de planeio entre aproximadamente 5 e 15 m. O mesmo pipeline
é utilizado pelo núcleo Python, API, interface, casos demonstrativos e gerador
de variantes.

> **Aviso técnico obrigatório:** os resultados são preliminares. O sistema não
> substitui o engenheiro responsável, software homologado, dados verificados,
> análise estrutural detalhada, CFD, ensaios, aprovação normativa ou
> classificadora.

## O que está funcional

- requisitos classificados, matriz de aderência e gate obrigatório;
- pesos, momentos, LCG, TCG, VCG, grupos, margens e confiança;
- condições de carregamento, pessoas, carga e tanques;
- casco paramétrico em V e malha usada pela visualização 3D;
- hidrostática por integração numérica de seções;
- solução simultânea de peso–empuxo e LCB–LCG;
- calado médio, calados extremos, trim e borda livre;
- GM transversal/longitudinal e superfície livre;
- curva GZ preliminar explicitamente marcada como estimativa;
- resistência/planeio preliminar inspirada em Savitsky e fricção ITTC-1957;
- potência efetiva, entregue e instalada com margens explícitas;
- banco demonstrativo e combinações de motores compatíveis;
- combustível, consumo, autonomia, alcance e raio de ação;
- estimativas estruturais preliminares para três materiais;
- nove variantes demonstrativas pelo mesmo pipeline;
- seleção NF-ECO, NF-BALANCED e NF-PERFORMANCE;
- relatórios PDF, DOCX, XLSX, CSV e JSON;
- FastAPI, PostgreSQL, SQLAlchemy, Alembic, Redis e Celery;
- PWA React/TypeScript, Three.js e Plotly, instalável e responsiva;
- três projetos demonstrativos sintéticos: 7 m, 10 m e 12 m;
- Docker Compose, testes, CI e scripts Windows/Linux.

## Implantação pública recomendada

O repositório inclui `render.yaml` para publicar a API Docker no Render e usar
PostgreSQL persistente no Neon, mantendo a PWA no Cloudflare Pages. Essa
configuração desativa Celery/Redis inicialmente e executa jobs de forma síncrona
para caber no ambiente demonstrativo gratuito.

Siga o passo a passo em [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md). Nunca grave a
`DATABASE_URL` do Neon no GitHub; ela deve ser cadastrada como segredo no Render.

Serviços demonstrativos publicados:

- PWA: <https://navalforgeconcept.pages.dev>
- API: <https://navalforge-concept-api.onrender.com>
- prontidão da API e banco: <https://navalforge-concept-api.onrender.com/ready>
- documentação OpenAPI: <https://navalforge-concept-api.onrender.com/docs>

## Execução mais simples — Docker

Requisitos: Docker Desktop no Windows ou Docker Engine + Compose no Linux.

```bash
cp .env.example .env
docker compose up --build
```

Abra:

- interface: <http://localhost:8080>
- API: <http://localhost:8000>
- documentação OpenAPI: <http://localhost:8000/docs>
- saúde do backend: <http://localhost:8000/health>

Para encerrar:

```bash
docker compose down
```

## Execução local sem Docker

### Linux

```bash
chmod +x scripts/start_linux.sh
./scripts/start_linux.sh
```

### Windows PowerShell

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\start_windows.ps1
```

### Manualmente

Backend:

```bash
python -m venv .venv
# Linux: source .venv/bin/activate
# Windows: .venv\Scripts\activate
pip install -e ".[api,dev]"
python scripts/seed_examples.py
uvicorn backend.app.main:app --reload
```

Frontend em outro terminal:

```bash
cd frontend
npm install
# Linux/macOS
VITE_API_URL=http://localhost:8000 npm run dev
# Windows PowerShell
$env:VITE_API_URL="http://localhost:8000"; npm run dev
```

## PWA instalável

A interface conserva três resultados previamente calculados para contingência
offline. A distribuição pública 0.1.6 é compilada com a API do Render:

```bash
cd frontend
npm install
VITE_API_URL=https://navalforge-concept-api.onrender.com npm run build
npm run preview
```

Acesse o endereço mostrado, visite uma vez conectado e use **Instalar app**.
Quando `VITE_API_URL` contiver a API pública, o botão **Executar projeto** realiza
um novo cálculo no backend e o selo muda para **BACKEND ONLINE**. Quando a
variável estiver vazia, ou se o backend ficar indisponível, a PWA usa o caso
offline sem tentar interpretar respostas HTML como JSON.

Consulte [docs/MOBILE_PWA.md](docs/MOBILE_PWA.md) para Android e publicação.

## Uso do núcleo Python

```python
import json
from pathlib import Path

from navalforge_core import Project, avaliar_projeto

dados = json.loads(Path("examples/nf-demo-service-7m.json").read_text())
projeto = Project.model_validate(dados)
resultado = avaliar_projeto(projeto)

print(resultado["status"])
print(resultado["indicators"])
print(resultado["selected_alternatives"])
```

A estrutura de saída inclui:

```json
{
  "project_id": "...",
  "revision": "...",
  "status": "...",
  "results": {},
  "requirements": {},
  "conformities": [],
  "non_conformities": [],
  "warnings": [],
  "assumptions": [],
  "margins": {},
  "indicators": {},
  "traceability": {},
  "variants": [],
  "selected_alternatives": {
    "eco": {},
    "balanced": {},
    "performance": {}
  }
}
```

Uma pontuação alta nunca mascara falha obrigatória. Quando um requisito
obrigatório falha, o status contém:

**NÃO CONFORME — requisito obrigatório não atendido.**

## API principal

| Método | Rota | Função |
|---|---|---|
| `GET` | `/health` | saúde e versão |
| `GET` | `/ready` | saúde da API e conexão com o banco |
| `GET` | `/api/v1/projects/demo` | três projetos sintéticos |
| `GET` | `/api/v1/projects` | projetos persistidos |
| `PUT` | `/api/v1/projects/{id}` | cria/atualiza projeto |
| `POST` | `/api/v1/evaluate` | cálculo síncrono |
| `POST` | `/api/v1/jobs` | cálculo por job |
| `GET` | `/api/v1/jobs/{id}` | consulta do job |
| `GET` | `/api/v1/engines` | banco demonstrativo |
| `POST` | `/api/v1/reports` | exportação de relatório |

## Estrutura do repositório

```text
navalforge-concept/
├── navalforge_core/        # núcleo de engenharia independente
├── backend/                # FastAPI, SQLAlchemy, Alembic e Celery
├── frontend/               # React, TypeScript, Three.js, Plotly e PWA
├── databases/              # motores, materiais, equipamentos e regras demo
├── examples/               # projetos e relatórios sintéticos
├── tests/                  # testes de cálculo e integração do pipeline
├── docs/                   # métodos, implantação e validação
├── scripts/                # geração, sincronização e verificação
├── docker-compose.yml
├── pyproject.toml
└── .env.example
```

## Testes e verificação

```bash
PYTHONPATH=. python -m unittest discover -s tests -v
cd frontend && npm run typecheck && npm run lint && npm run build
cd ..
PYTHONPATH=. python scripts/verify_project.py
docker compose config --quiet
```

Os testes verificam coerência de unidades, validação de entradas, simetria,
volume crescente com calado, equilíbrio peso–empuxo, LCB–LCG, superfície livre,
identidade de GM, tendência de potência, gate obrigatório, variantes, orientação
Y-up da malha e geração de relatórios. Eles validam o comportamento do software,
não a precisão de um projeto real.

## Projetos demonstrativos

Todos os dados são sintéticos e identificados como demonstração:

- `NF-DEMO-SERVICE-7M` — lancha de serviço em alumínio;
- `NF-DEMO-PATROL-10M` — lancha de patrulha com hidrojato;
- `NF-DEMO-RESCUE-12M` — embarcação de resgate/apoio em compósito.

Relatórios ficam em `examples/generated/` e também são empacotados na PWA.

## Limitações reais da versão 0.1.6

- casco paramétrico simplificado; offsets verificados ainda não dirigem toda a interface;
- curva GZ por aproximação de costados verticais, não geometria inclinada completa;
- resistência é triagem conceitual inspirada em Savitsky, não implementação certificada;
- porpoising é indicador heurístico;
- motores, dimensões, prazos e preços são demonstrativos;
- estrutura usa triagem de placa e não regra completa de classe;
- importação DXF/STL/STEP/IGES/Rhino/DELFTship está preparada como evolução;
- não há CFD, FEA ou estabilidade avariada automática nesta versão;
- autenticação multiusuário e armazenamento de objetos exigem implantação adicional;
- critérios normativos precisam ser selecionados e configurados pelo engenheiro.

## Próximo incremento recomendado

1. Tornar requisitos, geometria, pesos e condições totalmente editáveis na PWA.
2. Adicionar autenticação e separar projetos por usuário/organização.
3. Habilitar Redis/Celery para jobs pesados fora do plano demonstrativo gratuito.
4. Importar offsets e malhas verificadas.
5. Validar módulo a módulo com cálculos manuais, exemplos publicados e ensaios.
6. Integrar o módulo CFD/OpenFOAM como job pesado separado.

## Licença

Código: [GNU AGPL v3](LICENSE). A licença não representa validação técnica,
aprovação normativa ou autorização para uso de dados confidenciais.
