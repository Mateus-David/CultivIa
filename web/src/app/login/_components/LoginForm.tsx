// LoginForm — pede o token e confere na API.
//
// O token é o API_TOKEN do .env. Guardamos no sessionStorage e testamos com
// GET /api/login: 200 = certo (vai para o painel), 401 = errado.
"use client";

import { useRouter } from "next/navigation";
import { useState, type SubmitEvent } from "react";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { api, mensagemDeErro } from "@/lib/api";
import { token } from "@/lib/token";

export function LoginForm() {
  const router = useRouter();
  const [valor, setValor] = useState("");        // o que está digitado
  const [erro, setErro] = useState("");
  const [enviando, setEnviando] = useState(false);

  async function entrar(e: SubmitEvent<HTMLFormElement>) {
    e.preventDefault();   // impede o navegador de recarregar a página
    setEnviando(true);
    token.salvar(valor.trim());
    try {
      await api.testarLogin();
      router.replace("/");
    } catch (err) {
      setErro(mensagemDeErro(err));
    } finally {
      setEnviando(false);   // `finally` roda com sucesso OU erro
    }
  }

  return (
    <form onSubmit={entrar} className="mx-auto mt-[20vh] max-w-xs">
      <Card>
        <h1 className="text-center text-2xl font-bold">CultivIa</h1>
        {/* Campo CONTROLADO: o valor vem do estado e cada tecla atualiza o estado */}
        <input
          type="password"
          placeholder="Token de acesso"
          value={valor}
          onChange={(e) => setValor(e.target.value)}
          autoFocus
          className="rounded-lg border border-borda bg-fundo p-2.5 outline-none focus:border-verde"
        />
        <Button type="submit" disabled={enviando || !valor}>
          {enviando ? "Entrando..." : "Entrar"}
        </Button>
        {erro && <p className="text-center text-vermelho">{erro}</p>}
      </Card>
    </form>
  );
}
