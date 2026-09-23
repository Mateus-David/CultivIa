// Painel — a tela principal. Junta os hooks (dados) com os cards (visual).
//
// "use client": este componente usa estado, efeitos e eventos, então precisa
// rodar no NAVEGADOR. Tudo que ele importa (cards, hooks) vira cliente
// também, por isso só precisamos da diretiva aqui na "fronteira".
//
// COMO OS DADOS ANDAM:
//   LER:     useEstado -> api.estado() a cada 2 s -> `estado` -> cards
//   ENVIAR:  card chama onXxx -> executar(api.xxx) -> API -> MQTT -> placa
"use client";

import { useRouter } from "next/navigation";
import { useComando } from "@/hooks/useComando";
import { useEstado } from "@/hooks/useEstado";
import { api } from "@/lib/api";
import { token } from "@/lib/token";
import { AtuadoresCard } from "./AtuadoresCard";
import { Cabecalho } from "./Cabecalho";
import { EnvioCard } from "./EnvioCard";
import { GrafanaCard } from "./GrafanaCard";
import { LeiturasCard } from "./LeiturasCard";
import { SimulacaoCard } from "./SimulacaoCard";

export function Painel() {
  const router = useRouter();
  const { estado, erro: erroLeitura, atualizar } = useEstado();
  const { executar, erro: erroComando } = useComando(atualizar);

  // Valores DERIVADOS: calculados do estado a cada desenho (não são useState)
  const online = estado?.placa_online ?? false;   // `??` = "se for null, use false"
  const dispositivo = estado?.dispositivo ?? null;
  const erro = erroComando || erroLeitura;

  function sair() {
    token.apagar();
    router.replace("/login");
  }

  return (
    <div className="mx-auto max-w-6xl">
      <Cabecalho online={online} onSair={sair} />
      {erro && <p className="mb-4 text-center text-vermelho">{erro}</p>}

      {/* Grade responsiva: quantas colunas de pelo menos 260px couberem
          (no celular vira 1 coluna sozinha). */}
      <main className="grid grid-cols-[repeat(auto-fit,minmax(260px,1fr))] gap-4">
        <LeiturasCard sensores={estado?.sensores ?? null} />
        <AtuadoresCard
          dispositivo={dispositivo}
          habilitado={online}
          onAlternar={(nome, ligar) => executar(() => api.alternarAtuador(nome, ligar))}
        />
        <SimulacaoCard
          atual={dispositivo?.setpoint}
          habilitado={online}
          onAplicar={(alvo) => executar(() => api.definirSetpoint(alvo))}
        />
        <EnvioCard
          atual={dispositivo?.envio}
          habilitado={online}
          onConfigurar={(envio) => executar(() => api.configurarEnvio(envio))}
        />
      </main>

      <GrafanaCard />
    </div>
  );
}
