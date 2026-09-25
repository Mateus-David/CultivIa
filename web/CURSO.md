# Curso: o site do CultivIa, caminho a caminho

Este guia não explica arquivo por arquivo. Ele segue **o caminho que os dados
fazem**, parada por parada, e apresenta cada conceito de React/TypeScript
**no momento em que ele aparece**. No fim de cada módulo há um exercício para
você ver aquilo acontecendo com os próprios olhos.

Leia com o código aberto do lado: todo link `arquivo:linha` abre o ponto exato.

| Módulo | Pergunta que ele responde |
|---|---|
| [0. O mapa](#módulo-0--o-mapa) | Quem são as peças e quem fala com quem? |
| [1. Abrir a página](#módulo-1--abrir-a-página) | O que acontece quando digito o endereço do site? |
| [2. Ler o estado](#módulo-2--ler-o-estado-a-cada-2-s) | Como a tela sabe o que a placa está fazendo? |
| [3. Enviar um alvo](#módulo-3--enviar-um-alvo-para-a-placa) | O que acontece quando clico em "Enviar para a placa"? |
| [4. Os gráficos](#módulo-4--os-gráficos-grafana) | De onde vêm os gráficos? |
| [5. Por que tantos arquivos?](#módulo-5--por-que-tantos-arquivos) | Onde mexo para mudar X? |
| [Glossário](#glossário) | O que é `??`, `...`, `useCallback`...? |
| [Desafios](#desafios) | Agora faça você |

---

## Módulo 0 — O mapa

O site tem **4 caminhos**, e só 4. Todo o resto é detalhe de um deles:

```
 1. ABRIR A PÁGINA     navegador ──GET /──────────────▶ Next.js (web)
 2. LER O ESTADO       navegador ──GET /api/estado────▶ Next.js ─▶ API ─▶ memória ◀─ MQTT ◀─ placa
 3. ENVIAR UM ALVO     navegador ──POST /api/setpoint─▶ Next.js ─▶ API ─▶ MQTT ─▶ placa
 4. VER OS GRÁFICOS    navegador ──iframe :3000───────▶ Grafana ◀─ InfluxDB ◀─ Telegraf ◀─ MQTT ◀─ placa
```

As peças (todas são containers do [docker-compose.yml](../docker-compose.yml)):

| Peça | Porta | O que faz | Fala |
|---|---|---|---|
| **Navegador** | — | Mostra a tela, roda o React | só HTTP |
| **web** (Next.js) | 8080 | Entrega a página e **repassa** `/api/*` para a API | HTTP |
| **api** (FastAPI) | 8000 | Tradutor: HTTP de um lado, MQTT do outro | HTTP + MQTT |
| **mosquitto** | 1883 | Correio do MQTT: recebe e distribui mensagens | MQTT |
| **placa** (BitDogLab) | — | Publica leituras, obedece aos alvos | só MQTT |
| **grafana** | 3000 | Desenha os gráficos (dentro de um iframe no site) | HTTP |

> **A ideia central:** o navegador só sabe falar HTTP e a placa só sabe falar
> MQTT. Eles nunca conversam direto. A API existe **só** para traduzir.

### Os arquivos do site, na ordem em que o código é executado

```
web/
├── next.config.ts                     (caminho 2 e 3) repassa /api → API
└── src/
    ├── app/
    │   ├── layout.tsx                 (caminho 1) <html> e <body> de toda página
    │   ├── globals.css                (caminho 1) Tailwind + cores do projeto
    │   ├── icon.svg                   (caminho 1) ícone da aba
    │   └── (painel)/
    │       ├── page.tsx               (caminho 1) rota "/" — só chama o Painel
    │       └── _components/
    │           ├── Painel.tsx         ★ o "centro": liga hooks e cards
    │           ├── Logo.tsx           (caminho 1) desenho + nome
    │           ├── ParametrosCard.tsx (caminho 2 e 3) sliders + botão
    │           └── GrafanaCard.tsx    (caminho 4) o iframe
    ├── components/ui/                 peças visuais genéricas
    │   ├── Card.tsx  Button.tsx  Slider.tsx
    ├── hooks/
    │   ├── useEstado.ts               (caminho 2) pergunta à API a cada 2 s
    │   └── useComando.ts              (caminho 3) envia e trata erro
    └── lib/
        ├── api.ts                     (caminho 2 e 3) o ÚNICO lugar que faz fetch
        └── types.ts                   formato do JSON que a API devolve
```

Se for ler um arquivo só, leia o [Painel.tsx](<src/app/(painel)/_components/Painel.tsx>):
ele tem 38 linhas e é o ponto onde os 4 caminhos se encontram.

---

## Módulo 1 — Abrir a página

Você digita `http://<IP>:8080`. Vamos seguir esse pedido.

### Parada 1 · O Docker entrega o pedido ao Next.js

A porta 8080 do PC é ligada à porta 3000 do container `web`
([docker-compose.yml](../docker-compose.yml), serviço `web`: `"8080:3000"`).
Lá dentro roda `node server.js`, o servidor que o Next.js gerou no build
([Dockerfile](Dockerfile), último estágio).

### Parada 2 · O Next.js descobre qual arquivo é a página `/`

No **App Router**, as pastas dentro de `src/app/` viram URLs:

```
src/app/(painel)/page.tsx   →   /
```

A pasta `(painel)` tem parênteses: é um **grupo de rotas**. Serve só para
organizar e **não entra na URL**. Por isso a página é `/` e não `/painel`.

### Parada 3 · O layout embrulha a página

[layout.tsx:24-30](src/app/layout.tsx#L24-L30) é a moldura de toda página:

```tsx
export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="pt-BR">
      <body className="...">{children}</body>   // ← children = a página
    </html>
  );
}
```

> **Conceito: componente.** Um componente React é **uma função que devolve
> HTML** (tecnicamente, JSX — HTML dentro do JavaScript). `RootLayout` é um;
> `Painel`, `Card`, `Button` também. Nome sempre com letra maiúscula.

> **Conceito: `children`.** É o que fica *entre* as tags quando você usa o
> componente: em `<Card>oi</Card>`, `children` é `"oi"`. Aqui o Next.js
> coloca a página da rota atual dentro do layout.

O layout também importa o [globals.css](src/app/globals.css) (uma vez só,
para o site inteiro) e define o `<title>` via `metadata`.

### Parada 4 · A página só chama o Painel

[page.tsx:10-12](<src/app/(painel)/page.tsx#L10-L12>):

```tsx
export default function PaginaPainel() {
  return <Painel />;
}
```

Parece inútil, mas tem um motivo: é a fronteira entre **servidor** e
**navegador**.

> **Conceito: Server Component × Client Component.**
> Por padrão, no Next.js, um componente é de **servidor**: roda só no Node,
> vira HTML e pronto — não pode ter botão que reage, timer, nada interativo.
> Quando o arquivo começa com `"use client"`, o componente é de **cliente**:
> o JavaScript dele também vai para o navegador, e aí pode usar estado,
> efeitos e cliques.
>
> O [Painel.tsx:10](<src/app/(painel)/_components/Painel.tsx#L10>) tem
> `"use client"`. Tudo que ele importa vira cliente junto, por isso a diretiva
> só aparece nele.

**Detalhe que confunde:** componente de cliente **também** é desenhado uma vez
no servidor (para o HTML chegar pronto). Depois o navegador baixa o JS e
"acorda" esse HTML — isso se chama **hidratação**. Guarde isso: vai explicar
duas coisas mais à frente (o "offline" que pisca ao abrir e o `useEffect` do
Grafana).

### Parada 5 · O Painel monta a tela

[Painel.tsx:24-37](<src/app/(painel)/_components/Painel.tsx#L24-L37>):

```tsx
<div className="mx-auto flex max-w-6xl flex-col gap-4">
  <header><Logo /></header>
  {erro && <p className="text-vermelho">{erro}</p>}      // só aparece se houver erro
  <ParametrosCard naPlaca={...} online={...} onEnviar={...} />
  <GrafanaCard />
</div>
```

De cima para baixo: logo, mensagem de erro (se houver), card dos parâmetros,
dashboard. É **exatamente** o que você vê na tela.

> **Conceito: props.** São os "parâmetros" de um componente, passados como
> atributos: `<ParametrosCard online={true} />`. Do lado de dentro, o
> componente recebe um objeto `{ online }`. Os tipos das props ficam num
> `type ...Props` logo acima do componente
> ([ParametrosCard.tsx:15-19](<src/app/(painel)/_components/ParametrosCard.tsx#L15-L19>)).

> **Conceito: `{cond && <X />}`.** Desenho condicional: se `cond` for falso
> (ou string vazia), não desenha nada.

### Parada 6 · O visual: Tailwind

Não há arquivo CSS por componente. O visual está nas classes:
`className="rounded-xl border border-borda bg-cartao p-4"`. Cada classe é uma
regra pequena (`p-4` = padding, `rounded-xl` = cantos arredondados...).

As cores com nome do projeto (`bg-cartao`, `text-verde`, `border-borda`) vêm
de [globals.css:10-19](src/app/globals.css#L10-L19): cada `--color-X` vira
`bg-X`, `text-X`, `border-X`.

### ✍️ Exercício 1

1. `cd web && npm run dev` e abra `http://localhost:3001`.
2. Em [globals.css](src/app/globals.css), troque `--color-verde` por `#60a5fa`
   (azul) e salve. O site inteiro muda sem recarregar. Desfaça.
3. No [Painel.tsx](<src/app/(painel)/_components/Painel.tsx>), troque a ordem
   de `<ParametrosCard>` e `<GrafanaCard />`. Veja a tela. Desfaça.

---

## Módulo 2 — Ler o estado (a cada 2 s)

A página abriu. Como ela descobre se a placa está online e quais alvos ela
está usando? **Perguntando**, a cada 2 segundos. Isso se chama **polling**.

O caminho completo de uma pergunta, ida e volta:

```
 NAVEGADOR                           │ SERVIDORES
                                     │
 Painel                              │
  └ useEstado()        [parada 1-2]  │
     └ a cada 2 s: atualizar()       │
        └ api.estado() [parada 3]    │
           └ fetch("/api/estado") ───┼──▶ Next.js  rewrites      [parada 4]
                                     │     └──▶ API GET /estado  [parada 5]
                                     │           └ lê a MEMÓRIA ◀── on_message ◀── Mosquitto ◀── placa
                                     │                              [parada 6]
           ◀─── JSON ────────────────┼───────────┘
        setEstado(json)  [parada 7]  │
  Painel redesenha → ParametrosCard mostra "Placa usando 25 °C e 40 %"
```

### Parada 1 · O Painel pede o estado

[Painel.tsx:20](<src/app/(painel)/_components/Painel.tsx#L20>):

```tsx
const { estado, erro: erroLeitura, atualizar } = useEstado();
```

Uma linha. Toda a lógica de "perguntar a cada 2 s" está escondida em
`useEstado`.

> **Conceito: hook.** Função que começa com `use` e pode usar os recursos do
> React (estado, efeitos). Um **hook próprio** como `useEstado` serve para
> tirar lógica de dentro do componente: o Painel não sabe *como* o estado é
> buscado, só recebe `estado` pronto.
>
> `erro: erroLeitura` é só renomear: o hook devolve `erro`, e aqui ele passa
> a se chamar `erroLeitura` (porque o `useComando` também tem um `erro`).

### Parada 2 · `useEstado` liga um timer

[useEstado.ts:12-36](src/hooks/useEstado.ts#L12-L36). Três peças:

**a) O estado — `useState`** (linhas 13-14)

```ts
const [estado, setEstado] = useState<Estado | null>(null);  // começa null
const [erro, setErro] = useState("");
```

> **Conceito: estado (`useState`).** É uma variável que o React **vigia**.
> Você nunca muda `estado` direto; chama `setEstado(novo)`. Quando faz isso,
> o React **redesenha** o componente com o valor novo. É assim que a tela se
> atualiza sozinha: ninguém mexe no HTML na mão.
>
> Uma variável comum (`let x = 1`) não serve: ela some a cada redesenho e,
> se mudar, a tela não fica sabendo.

**b) A função que busca — `atualizar`** (linhas 18-25)

```ts
const atualizar = useCallback(async () => {
  try {
    setEstado(await api.estado());   // deu certo: guarda o JSON
    setErro("");
  } catch (e) {
    setErro(mensagemDeErro(e));      // deu errado: guarda a frase de erro
  }
}, []);
```

> **Conceito: `async` / `await`.** Pedir algo pela rede demora. `await`
> significa "espere a resposta chegar e depois continue". Só pode ser usado
> dentro de função `async`.

O `useCallback` você pode ignorar por enquanto: ele só garante que
`atualizar` seja **a mesma função** entre um redesenho e outro (veja no
[glossário](#glossário) por que isso importa).

**c) O timer — `useEffect`** (linhas 29-33)

```ts
useEffect(() => {
  atualizar();                                  // pergunta já
  const id = setInterval(atualizar, intervaloMs);  // e depois a cada 2000 ms
  return () => clearInterval(id);               // LIMPEZA: desliga o timer
}, [atualizar, intervaloMs]);
```

> **Conceito: efeito (`useEffect`).** Código que roda **depois** que o
> componente aparece na tela, e **só no navegador** (nunca no servidor).
> Serve para coisas "de fora" do React: timers, rede, `window`.
>
> - O `return () => ...` é a **limpeza**: roda quando o componente some.
>   Sem ela, o timer continuaria rodando para sempre.
> - O `[atualizar, intervaloMs]` é a **lista de dependências**: o efeito roda
>   de novo só se uma delas mudar. Como nenhuma muda, roda uma vez só.

Lembra da hidratação? No servidor o efeito **não roda**, então `estado` é
`null` no HTML inicial. Por isso, no primeiro instante, a tela mostra
"Placa offline" até a primeira resposta chegar.

### Parada 3 · `api.estado()` faz o `fetch`

[api.ts:45-46](src/lib/api.ts#L45-L46):

```ts
export const api = {
  estado: () => requisitar<Estado>("/estado"),
  ...
```

E `requisitar` ([api.ts:19-34](src/lib/api.ts#L19-L34)) é onde o pedido HTTP
realmente sai:

```ts
const resposta = await fetch(`/api${caminho}`, { method, headers, body });
if (!resposta.ok) { ... throw new ErroApi(detalhe); }   // 4xx/5xx vira erro
return resposta.json();                                 // texto JSON → objeto
```

Repare: o endereço é `/api/estado`, **sem** IP nem porta. O navegador manda
para o mesmo servidor que entregou a página (o Next.js, porta 8080).

> **Por que um arquivo só para isso?** Para existir **um único** lugar que
> fala com o servidor. Se amanhã a API mudar de endereço ou precisar de um
> cabeçalho novo, você mexe só aqui.

> **Conceito: `<Estado>` (generic).** `requisitar<Estado>` diz ao TypeScript:
> "o JSON que volta tem o formato `Estado`". Com isso, lá no Painel, o editor
> sabe que existe `estado.placa_online` e reclama se você escrever
> `estado.placa_onlin`. O formato está em [types.ts:30-36](src/lib/types.ts#L30-L36).
> **Atenção:** isso é só uma promessa para o editor; ninguém confere o JSON
> de verdade em tempo de execução.

### Parada 4 · O Next.js repassa para a API

[next.config.ts:17-19](next.config.ts#L17-L19):

```ts
async rewrites() {
  return [{ source: "/api/:caminho*", destination: `${API_URL}/:caminho*` }];
}
```

Tradução: "tudo que chegar em `/api/QUALQUER_COISA`, repasse para
`API_URL/QUALQUER_COISA`". O `/api` é **retirado** no caminho:

```
navegador:  GET http://10.80.102.72:8080/api/estado
Next.js:    GET http://api:8000/estado          (api = nome do container)
```

Por que não chamar a API direto do navegador? Porque aí seriam dois endereços
diferentes (8080 e 8000), e o navegador bloqueia isso por segurança (**CORS**)
a não ser que a API seja configurada para liberar. Passando tudo pelo Next.js,
para o navegador é **um endereço só**.

`API_URL` vem do [Dockerfile](Dockerfile) (`http://api:8000`) e é lida na
**build**. No `npm run dev` ela não existe, então vale `http://localhost:8000`.

### Parada 5 · A API responde com o que tem na memória

Agora estamos no Python. [routes.py:23-34](../api/app/routes.py#L23-L34):

```python
@router.get("/estado")
def estado() -> Estado:
    m = mqtt.memoria
    return Estado(
        placa_online=m.placa_online(),
        mqtt=mqtt.conectado(),
        recebido_ha_s=m.idade_leitura(),
        sensores=m.sensores,
        dispositivo=m.dispositivo,
    )
```

Ponto-chave: a API **não pergunta nada à placa** nessa hora. Ela só devolve
a última coisa que recebeu e guardou na memória. A resposta real é assim:

```json
{
  "placa_online": true,
  "mqtt": true,
  "recebido_ha_s": 0.6,
  "sensores": {"modo": "joystick", "temperatura_simulada": 25.0, "umidade_simulada": 50.0,
               "temperatura_ideal": 25.0, "umidade_ideal": 40.0, "...": "..."},
  "dispositivo": {"online": 1, "setpoint": {"temperatura": 25.0, "umidade": 40.0}}
}
```

### Parada 6 · Quem enche essa memória?

Um cliente MQTT que roda **em paralelo** dentro da API, desde que ela sobe
([main.py:28-32](../api/app/main.py#L28-L32) liga, [mqtt.py:84-88](../api/app/mqtt.py#L84-L88)
conecta). Ele assina dois tópicos ([mqtt.py:57](../api/app/mqtt.py#L57)) e,
a cada mensagem, guarda na memória ([mqtt.py:60-71](../api/app/mqtt.py#L60-L71)):

| Tópico | Quem publica | Quando | Vai para |
|---|---|---|---|
| `cultivia/sensores` | placa | a cada 2 s | `memoria.sensores` |
| `cultivia/estado` | placa | ao conectar e quando o alvo muda (**retido**) | `memoria.dispositivo` |
| `cultivia/estado` = `{"online": 0}` | o **Mosquitto**, em nome da placa | quando a placa cai (**Last Will**) | `memoria.dispositivo` |

> **Retido** = o Mosquitto guarda a última mensagem daquele tópico e entrega
> a quem assinar depois. Se a API reiniciar, recebe o estado na hora.
>
> **Last Will** = "testamento": ao conectar, a placa deixa com o Mosquitto uma
> mensagem para publicar caso ela suma sem se despedir
> ([firmware main.py:338](../firmware/bitdoglab/main.py#L338)).

A regra de "online" é da API, não do site
([mqtt.py:36-44](../api/app/mqtt.py#L36-L44)): a placa disse `online: 1`
**e** mandou leitura há menos de 15 s. O site só obedece o `placa_online`.

### Parada 7 · A volta: o React redesenha

O JSON volta pelo mesmo caminho, `setEstado(json)` é chamado, e o React
redesenha o Painel. As props do card mudam
([Painel.tsx:30-34](<src/app/(painel)/_components/Painel.tsx#L30-L34>)):

```tsx
<ParametrosCard
  naPlaca={estado?.dispositivo?.setpoint}      // alvos que a placa confirmou
  online={estado?.placa_online ?? false}
  ...
```

> **Conceito: `?.` e `??`.**
> `estado?.dispositivo` = "se `estado` for `null`, pare e dê `undefined`, em
> vez de quebrar". `x ?? false` = "use `x`; se ele for `null`/`undefined`,
> use `false`". Juntos: enquanto nada chegou, `online` é `false`.

E o texto de status do card
([ParametrosCard.tsx:51-58](<src/app/(painel)/_components/ParametrosCard.tsx#L51-L58>))
escolhe entre "Placa offline", "Placa usando 25 °C e 40 %" ou "Placa online".

### ✍️ Exercício 2

1. Abra o site, aperte **F12 → aba Network (Rede)**. Veja um pedido
   `estado` aparecer a cada 2 s. Clique em um e olhe a aba **Response**: é o
   JSON da parada 5.
2. Pergunte você mesmo, sem o site:
   ```bash
   curl http://localhost:8080/api/estado   # passando pelo Next.js
   curl http://localhost:8000/estado       # direto na API (mesma resposta)
   ```
   (no PowerShell do Windows, use `curl.exe`.)
3. Veja as mensagens que **alimentam** a memória da API:
   ```bash
   docker exec cultivia-mosquitto sh -c 'mosquitto_sub -u api -P "$MQTT_API_PASSWORD" -i curso -t "cultivia/sensores" -t "cultivia/estado" -v'
   ```
   Mexa no joystick e veja os números mudarem. `Ctrl+C` para sair.
4. Desligue a placa (tire o USB). Conte quantos segundos até o site dizer
   "offline". Por que ~15 s e não na hora? (Resposta: parada 6 — quem
   percebe primeiro é a regra da API, "leitura com menos de 15 s". O Last
   Will demoraria mais: o Mosquitto só desiste da placa depois de 1,5 × o
   `keepalive=30` do firmware, uns 45 s.)
5. Em [Painel.tsx:20](<src/app/(painel)/_components/Painel.tsx#L20>), troque
   `useEstado()` por `useEstado(10000)` e veja o ritmo no Network mudar. Desfaça.

---

## Módulo 3 — Enviar um alvo para a placa

Agora o caminho inverso: você arrasta o slider para 28 °C e clica em
**"Enviar para a placa"**.

```
 NAVEGADOR                                    │ SERVIDORES
                                              │
 Slider  ──onChange(28)──▶ ParametrosCard     │
   [parada 1]              setEditado({28,40})│   (nada saiu do navegador ainda!)
                                              │
 Button ──onClick──▶ onEnviar(alvo)           │
   [parada 2]          │                      │
                       ▼                      │
 Painel:  executar(() => api.definirSetpoint(alvo))
   [parada 3-4]        │                      │
                       ▼                      │
 fetch POST /api/setpoint {"temperatura":28,"umidade":40}
   [parada 5]  ───────────────────────────────┼──▶ Next.js ─▶ API POST /setpoint   [parada 6]
                                              │         valida 0-50 / 0-100
                                              │         publica cultivia/comandos/setpoint (retido)
                                              │                 │
                                              │           Mosquitto ─▶ placa          [parada 7]
                                              │                      aplica o alvo
                                              │                      publica cultivia/estado
                                              │           Mosquitto ─▶ API memória    [parada 8]
 500 ms depois: atualizar() ── GET /api/estado┼──▶ ... (módulo 2 inteiro)
 texto: "Placa usando 28 °C e 40 %"           │
```

### Parada 1 · Arrastar o slider muda só o navegador

O [Slider.tsx:21-30](src/components/ui/Slider.tsx#L21-L30) é um
`<input type="range">`. Quando você arrasta:

```tsx
onChange={(e) => onChange(Number(e.target.value))}   // "28" (texto) → 28 (número)
```

Esse `onChange` foi passado pelo ParametrosCard
([ParametrosCard.tsx:36](<src/app/(painel)/_components/ParametrosCard.tsx#L36>)):

```tsx
onChange={(temperatura) => setEditado({ ...alvo, temperatura })}
```

> **Conceito: `...` (spread).** `{ ...alvo, temperatura }` = "copie todos os
> campos de `alvo` e troque só `temperatura`". Resultado:
> `{ temperatura: 28, umidade: 40 }`.

Agora o raciocínio mais importante do card
([ParametrosCard.tsx:23-24](<src/app/(painel)/_components/ParametrosCard.tsx#L23-L24>)):

```tsx
const [editado, setEditado] = useState<Setpoint | null>(null);
const alvo = editado ?? naPlaca ?? PADRAO;
```

O slider mostra **uma de três coisas**, nesta ordem de prioridade:

1. `editado` — o que **você** arrastou (se já arrastou);
2. `naPlaca` — o que a **placa** confirmou (vem do módulo 2);
3. `PADRAO` — 25 °C / 50 %, se nada chegou ainda.

Enquanto você não arrasta, `editado` é `null` e o slider **segue a placa**
(se alguém mudar o alvo nos botões A/B da BitDogLab, o slider anda sozinho).
Na primeira arrastada, ele passa a mostrar o seu valor.

> **Conceito: input controlado.** O slider não "guarda" a própria posição: ele
> mostra `value={valor}` e avisa quando alguém mexe (`onChange`). Quem decide
> o valor é o estado do React. Por isso, se você não chamar `setEditado`, o
> slider nem se move.

**Até aqui, nada saiu do seu navegador.**

### Parada 2 · O clique sobe para o Painel

[ParametrosCard.tsx:50](<src/app/(painel)/_components/ParametrosCard.tsx#L50>):

```tsx
<Button onClick={() => onEnviar(alvo)}>Enviar para a placa</Button>
```

O card **não sabe enviar nada**. Ele só avisa "clicaram, com este alvo"
chamando `onEnviar`, que veio de fora, do Painel.

> **Conceito: dados descem, eventos sobem.** No React, informação vai do pai
> para o filho por **props** (`naPlaca`, `online`). O filho avisa o pai por
> **funções que o pai passou** (`onEnviar`). Por isso o ParametrosCard é
> "burro" e fácil de entender: recebe valores, mostra, e avisa cliques.

### Parada 3 · O Painel decide o que fazer com o clique

[Painel.tsx:33](<src/app/(painel)/_components/Painel.tsx#L33>):

```tsx
onEnviar={(alvo) => executar(() => api.definirSetpoint(alvo))}
```

Leia de dentro para fora:
- `api.definirSetpoint(alvo)` — o pedido HTTP em si;
- `() => ...` — embrulhado numa função, **ainda não executada**;
- `executar(...)` — recebe essa função e a chama no momento certo, cuidando
  do erro e da atualização depois.

### Parada 4 · `useComando` executa, trata erro e agenda a atualização

[useComando.ts:16-27](src/hooks/useComando.ts#L16-L27):

```ts
const executar = useCallback(async (acao) => {
  try {
    await acao();                   // faz o POST e espera a resposta
    setErro("");
    setTimeout(aoConcluir, 500);    // daqui a 0,5 s: busca o estado de novo
  } catch (e) {
    setErro(mensagemDeErro(e));     // aparece em vermelho no topo do Painel
  }
}, [aoConcluir]);
```

`aoConcluir` é o `atualizar` do `useEstado` — o Painel ligou os dois na
[linha 21](<src/app/(painel)/_components/Painel.tsx#L21>):
`useComando(atualizar)`. Assim, depois de enviar, não é preciso esperar os 2 s
do próximo polling.

### Parada 5 · O POST sai do navegador

[api.ts:48-49](src/lib/api.ts#L48-L49):

```ts
definirSetpoint: (setpoint) => requisitar<Ok>("/setpoint", { method: "POST", corpo: setpoint }),
```

`requisitar` transforma `corpo` em texto JSON e manda
`POST /api/setpoint` com `{"temperatura":28,"umidade":40}`. O Next.js repassa
para `http://api:8000/setpoint` (mesma regra da parada 4 do módulo 2).

### Parada 6 · A API valida e publica no MQTT

[routes.py:37-47](../api/app/routes.py#L37-L47):

```python
@router.post("/setpoint")
def setpoint(corpo: ComandoSetpoint) -> Ok:
    dados = corpo.model_dump(exclude_none=True)
    ...
    mqtt.publicar_comando("setpoint", dados, retain=True)
    return Ok()
```

Antes mesmo da função rodar, o FastAPI confere o JSON contra
`ComandoSetpoint` ([schemas.py:18-23](../api/app/schemas.py#L18-L23)):
`temperatura` entre 0 e 50, `umidade` entre 0 e 100. Fora disso, responde
**422** e a função nem executa. É a proteção de verdade — o `min`/`max` do
slider pode ser burlado por qualquer um com `curl`.

Depois, `publicar_comando` ([mqtt.py:100-112](../api/app/mqtt.py#L100-L112))
publica em `cultivia/comandos/setpoint` com **retain**: se a placa estiver
desligada, o Mosquitto guarda e entrega quando ela ligar. É por isso que o
botão funciona mesmo com a placa offline.

E quem garante que só a API manda comandos? O [acl do Mosquitto](../mosquitto/config/acl):
o usuário `api` pode **escrever** em `cultivia/comandos/#`; a placa (`esp32`)
só pode **ler**.

### Parada 7 · A placa aplica e confirma

No firmware ([main.py:432](../firmware/bitdoglab/main.py#L432)), a cada volta
do loop a placa chama `check_msg()`. Chegou mensagem? O umqtt chama
`ao_receber` ([main.py:342-363](../firmware/bitdoglab/main.py#L342-L363)),
que atualiza `alvo_temp`/`alvo_umid` e marca `alvos_mudaram = True`. Na mesma
volta, `publicar_estado` ([main.py:386-392](../firmware/bitdoglab/main.py#L386-L392))
publica em `cultivia/estado`:

```json
{"online": 1, "setpoint": {"temperatura": 28.0, "umidade": 40.0}}
```

### Parada 8 · A confirmação volta para a tela

Daqui em diante é o **módulo 2 inteiro**: a API recebe `cultivia/estado`,
guarda em `memoria.dispositivo`; 500 ms depois do clique o site pergunta
`/api/estado`, recebe o setpoint novo, e o texto vira
"Placa usando 28 °C e 40 %".

> **Por que a tela mostra o que a placa confirmou, e não o que eu cliquei?**
> Porque o clique pode não ter chegado (placa offline, valor recusado...).
> O texto de status é a **verdade da placa**; o slider é o **seu rascunho**.

### Quando dá errado

Todo erro termina no mesmo lugar: a frase vermelha no topo do Painel
([Painel.tsx:22 e 29](<src/app/(painel)/_components/Painel.tsx#L22-L29>)).
Quem escreve a frase é `mensagemDeErro` ([api.ts:37-40](src/lib/api.ts#L37-L40)).

| O que aconteceu | Resposta | Frase na tela |
|---|---|---|
| API parada / sem rede | `fetch` nem completa | "Sem conexão com a API" |
| Valor fora da faixa | 422 (o `detail` vem como lista) | "Erro 422" |
| API sem conexão com o Mosquitto | 503 | "Broker MQTT indisponível" |
| Placa offline | 200 (o broker guardou) | nenhuma — o card diz "recebe quando conectar" |

### ✍️ Exercício 3

1. Num terminal, "escute" o tópico de comandos (como usuário `esp32`, que
   pode lê-lo; `-i` é um nome diferente do da placa para não derrubá-la):
   ```bash
   docker exec cultivia-mosquitto sh -c 'mosquitto_sub -u esp32 -P "$MQTT_ESP32_PASSWORD" -i curso-cmd -t "cultivia/comandos/#" -v'
   ```
   A primeira linha aparece na hora: é a mensagem **retida**. Agora envie um
   alvo pelo site e veja a nova chegar.
2. Com o F12 → Network aberto, clique em "Enviar". Veja o `setpoint` (POST)
   e, meio segundo depois, um `estado` extra fora do ritmo de 2 s.
3. Tente burlar o slider:
   ```bash
   curl -X POST http://localhost:8080/api/setpoint -H "Content-Type: application/json" -d '{"temperatura": 80}'
   ```
   Leia o 422. Qual arquivo recusou? (Resposta: [schemas.py](../api/app/schemas.py#L22)).
4. Arraste o slider **sem** enviar e depois mude o alvo pelos botões A/B da
   placa. O texto de status muda, o slider não. Por quê? (Resposta: parada 1 —
   `editado` já não é `null`.)

---

## Módulo 4 — Os gráficos (Grafana)

Este caminho **não passa pela API nem pelo React**. O
[GrafanaCard.tsx](<src/app/(painel)/_components/GrafanaCard.tsx>) só coloca
um `<iframe>` — uma "janela" para outra página — e o navegador carrega o
Grafana lá dentro.

```
placa ─▶ Mosquitto ─▶ Telegraf ─▶ InfluxDB ─▶ Grafana :3000 ─▶ <iframe> no site
         cultivia/     grava a      guarda o     consulta e
         sensores      leitura      histórico    desenha
```

Os dados são os mesmos de `cultivia/sensores`, mas guardados com histórico
(a API só guarda a **última** leitura; o InfluxDB guarda **todas**).

### Por que a URL é montada dentro de um `useEffect`?

[GrafanaCard.tsx:13-22](<src/app/(painel)/_components/GrafanaCard.tsx#L13-L22>):

```tsx
function urlDoGrafana() {
  const { protocol, hostname } = window.location;   // o endereço que abriu o site
  return `${protocol}//${hostname}:3000/d/cultivia-estufa?orgId=1&kiosk&theme=dark&refresh=5s`;
}
...
const [url, setUrl] = useState<string | null>(null);
useEffect(() => setUrl(urlDoGrafana()), []);
```

- Usa o **mesmo host** que abriu o site (se você abriu pelo IP, o Grafana vem
  pelo IP; se foi `localhost`, vem por `localhost`). Nada de IP fixo no código.
- `window` só existe no navegador. Lembra da hidratação (módulo 1)? O
  componente também é desenhado no servidor, onde `window` não existe e o
  código quebraria. `useEffect` nunca roda no servidor — problema resolvido.
  Enquanto `url` é `null`, o iframe simplesmente não é desenhado.
- `kiosk` esconde os menus do Grafana; `refresh=5s` faz ele se atualizar sozinho.

E o Grafana só aceita aparecer num iframe, sem login, por causa de três
variáveis no serviço `grafana` do [docker-compose.yml](../docker-compose.yml):
`GF_SECURITY_ALLOW_EMBEDDING`, `GF_AUTH_ANONYMOUS_ENABLED` e
`GF_AUTH_ANONYMOUS_ORG_ROLE`.

### ✍️ Exercício 4

1. Clique com o botão direito dentro do gráfico → "Abrir quadro em nova aba".
   É a página do Grafana, sozinha.
2. Na URL dessa aba, tire o `&kiosk` e recarregue: aparecem os menus.

---

## Módulo 5 — Por que tantos arquivos?

Cada arquivo tem **uma** responsabilidade. Parece espalhado, mas a regra é:
se você sabe **o que** quer mudar, sabe **onde** mexer.

### "Quero mudar X" → mexa em Y

| Quero... | Arquivo |
|---|---|
| mudar uma cor do site inteiro | [globals.css](src/app/globals.css) |
| mudar o que aparece na tela / a ordem | [Painel.tsx](<src/app/(painel)/_components/Painel.tsx>) |
| mudar o card de parâmetros (textos, sliders) | [ParametrosCard.tsx](<src/app/(painel)/_components/ParametrosCard.tsx>) |
| mudar a aparência de **todos** os cards/botões | [Card.tsx](src/components/ui/Card.tsx), [Button.tsx](src/components/ui/Button.tsx) |
| mudar de quanto em quanto tempo o site pergunta | [useEstado.ts](src/hooks/useEstado.ts#L12) (`intervaloMs`) |
| chamar uma rota nova da API | [api.ts](src/lib/api.ts#L45) + [types.ts](src/lib/types.ts) |
| criar uma rota nova na API | [routes.py](../api/app/routes.py) + [schemas.py](../api/app/schemas.py) |
| mudar o que conta como "online" | [mqtt.py](../api/app/mqtt.py#L36) (API, não o site) |

### Os "contratos": coisas que precisam bater em mais de um lugar

Estes são os pontos onde o projeto quebra **em silêncio** se você mudar um
lado só:

| O quê | Tem que ser igual em |
|---|---|
| Formato do JSON de `/estado` | [schemas.py](../api/app/schemas.py) ↔ [types.ts](src/lib/types.ts) |
| Faixas 0-50 °C e 0-100 % | slider ([ParametrosCard.tsx](<src/app/(painel)/_components/ParametrosCard.tsx#L29-L45>)) ↔ [schemas.py](../api/app/schemas.py#L22-L23) ↔ `TEMP_MIN/MAX` no firmware |
| Alvo inicial 25 °C / 50 % | `PADRAO` ([ParametrosCard.tsx:13](<src/app/(painel)/_components/ParametrosCard.tsx#L13>)) ↔ `alvo_temp/alvo_umid` no [firmware](../firmware/bitdoglab/main.py#L151-L152) |
| Nomes dos tópicos MQTT | [config.py](../api/app/config.py#L20-L22) ↔ [firmware](../firmware/bitdoglab/main.py#L90-L91) ↔ [acl](../mosquitto/config/acl) |
| Prefixo `/api` | [api.ts](src/lib/api.ts#L20) ↔ [next.config.ts](next.config.ts#L18) |

### A regra das pastas

- `app/(painel)/_components/` → usado **só** por esta tela. O `_` diz ao
  Next.js "isto não é uma rota".
- `components/ui/` → peças genéricas, sem nada de "estufa" (Card não sabe o
  que é temperatura).
- `hooks/` → lógica com estado/efeito, sem HTML.
- `lib/` → código comum de TypeScript, sem React.

---

## Glossário

| Termo | O que é | Onde aparece |
|---|---|---|
| **componente** | função que devolve JSX; nome com maiúscula | todo `.tsx` |
| **JSX** | HTML escrito dentro do JS/TS; `{...}` insere valores | todo `.tsx` |
| **props** | parâmetros de um componente, passados como atributos | `<ParametrosCard online={...}>` |
| **children** | o que vai entre as tags `<Card>...</Card>` | [Card.tsx](src/components/ui/Card.tsx) |
| **estado** (`useState`) | variável vigiada; mudar com `setX` redesenha a tela | [useEstado.ts:13](src/hooks/useEstado.ts#L13) |
| **efeito** (`useEffect`) | código que roda depois de aparecer, só no navegador; o `return` limpa | [useEstado.ts:29](src/hooks/useEstado.ts#L29) |
| **hook** | função `useAlgo` que usa estado/efeitos; tira lógica do componente | [hooks/](src/hooks/) |
| **`useCallback`** | guarda a *mesma* função entre redesenhos. Sem ele, `atualizar` seria recriada a cada redesenho, o `useEffect` acharia que a dependência mudou e religaria o timer toda vez | [useEstado.ts:18](src/hooks/useEstado.ts#L18) |
| **`"use client"`** | este componente (e o que ele importa) também roda no navegador | [Painel.tsx:10](<src/app/(painel)/_components/Painel.tsx#L10>) |
| **hidratação** | o navegador "acorda" o HTML que veio do servidor, ligando cliques e efeitos | módulo 1 |
| **polling** | perguntar de tempos em tempos (o oposto: o servidor "empurrar") | módulo 2 |
| **rewrite** | o Next.js repassa um pedido para outro servidor, invisível ao navegador | [next.config.ts](next.config.ts) |
| **`async`/`await`** | esperar algo demorado (rede) sem travar a página | [api.ts](src/lib/api.ts) |
| **`?.`** | acessa se existir; se for `null`, dá `undefined` em vez de erro | [Painel.tsx:31](<src/app/(painel)/_components/Painel.tsx#L31>) |
| **`??`** | "use o da esquerda; se for `null`/`undefined`, use o da direita" | [ParametrosCard.tsx:24](<src/app/(painel)/_components/ParametrosCard.tsx#L24>) |
| **`...obj`** | copia os campos de um objeto para outro | [ParametrosCard.tsx:36](<src/app/(painel)/_components/ParametrosCard.tsx#L36>) |
| **`<T>`** (generic) | "o tipo aqui é T", escolhido por quem chama | [api.ts:19](src/lib/api.ts#L19) |
| **`type X = {...}`** | descreve o formato de um objeto (só para o editor) | [types.ts](src/lib/types.ts) |
| **retain** (MQTT) | o broker guarda a última mensagem e entrega a quem chegar depois | [mqtt.py:100](../api/app/mqtt.py#L100) |
| **Last Will** (MQTT) | mensagem que o broker publica se o cliente sumir sem avisar | [firmware main.py:338](../firmware/bitdoglab/main.py#L338) |

---

## Desafios

Para fixar, faça sem pedir para a IA. Cada um toca várias paradas do curso;
as dicas dizem quais.

**1. Os sliders voltam a seguir a placa depois de enviar.** Hoje, depois do
primeiro arraste, o slider nunca mais segue a placa (exercício 3.4).
Faça ele voltar a seguir depois de clicar em "Enviar".
*Dica: módulo 3, parada 1. Uma linha no `onClick` do botão, usando `setEditado`.*

**2. Mostrar a temperatura e a umidade atuais no card.** O JSON de `/estado`
já traz `sensores.temperatura_simulada` (módulo 2, parada 5), mas a tela não
mostra.
*Dica: o tipo já existe em [types.ts](src/lib/types.ts#L13). Passe
`estado?.sensores` do Painel para o ParametrosCard como uma prop nova (módulo 1,
parada 5) e desenhe com `?.` e `??`.*

**3. Botão desabilitado com a API fora do ar.** Se a API cair, o botão
continua clicável e só dá erro depois.
*Dica: o [Button](src/components/ui/Button.tsx) já aceita `disabled` e já
tem visual para isso. O Painel sabe se há erro de leitura (`erroLeitura`).*

**4. (Mais difícil) Mostrar "enviando..." enquanto o POST não volta.**
*Dica: um `useState` novo dentro de [useComando.ts](src/hooks/useComando.ts),
ligado antes do `await` e desligado depois (use `finally`). Devolva-o junto com
`executar` e `erro`.*

Depois de cada desafio, rode `npm run typecheck`: se você esqueceu de passar
uma prop ou errou um nome, o TypeScript aponta a linha.
