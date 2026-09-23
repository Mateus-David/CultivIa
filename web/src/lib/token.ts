// web/src/lib/token.ts — onde o token de acesso fica guardado no navegador.
//
// sessionStorage: memória do navegador que dura enquanto a aba estiver
// aberta e some ao fechá-la. Só existe no NAVEGADOR — por isso estas funções
// só podem ser chamadas em código que roda no cliente (eventos, useEffect).

const CHAVE = "cultivia_token";

export const token = {
  ler: () => sessionStorage.getItem(CHAVE),
  salvar: (valor: string) => sessionStorage.setItem(CHAVE, valor),
  apagar: () => sessionStorage.removeItem(CHAVE),
};
