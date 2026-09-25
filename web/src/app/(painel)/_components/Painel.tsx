"use client";

import { useComando } from "@/hooks/useComando";
import { useEstado } from "@/hooks/useEstado";
import { api } from "@/lib/api";
import { GrafanaCard } from "./GrafanaCard";
import { Logo } from "./Logo";
import { ParametrosCard } from "./ParametrosCard";

export function Painel() {
  const { estado, erro: erroLeitura, atualizar } = useEstado();
  const { executar, erro: erroComando } = useComando(atualizar);
  const erro = erroComando || erroLeitura;

  return (
    <div className="mx-auto flex max-w-6xl flex-col gap-4">
      <header className="pt-4">
        <Logo />
      </header>
      {erro && <p className="text-center text-vermelho">{erro}</p>}
      <ParametrosCard
        naPlaca={estado?.dispositivo?.setpoint}
        online={estado?.placa_online ?? false}
        onEnviar={(alvo) => executar(() => api.definirSetpoint(alvo))}
      />
      <GrafanaCard />
    </div>
  );
}
