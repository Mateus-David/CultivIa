// Rota "/" — o painel, protegido pelo login.
//
// A pasta "(painel)" tem parênteses: é um GRUPO DE ROTAS. Ela organiza os
// arquivos mas NÃO entra na URL — por isso esta página é "/" e não "/painel".
//
// Este arquivo é um Server Component (não tem "use client"): só monta a
// página. A parte interativa está em RequerLogin e Painel, que são de cliente.
import { RequerLogin } from "@/components/RequerLogin";
import { Painel } from "./_components/Painel";

export default function PaginaPainel() {
  return (
    <RequerLogin>
      <Painel />
    </RequerLogin>
  );
}
