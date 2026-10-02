# Process log — como cheguei na solução

Ferramenta principal: **Claude (Cowork)**, numa única conversa longa, com acesso a um ambiente Python/Node e ao meu computador. Abaixo, cada iteração: o que eu pedi, o que a IA fez, o que deu errado e o que mudou por causa disso. Os trechos da conversa (com minhas mensagens literais) estão em [`chat-exports/`](chat-exports/trechos-da-conversa.md); o histórico de commits desta branch mostra a construção.

---

## 1. Escolha do desafio

Pedi para a IA ler o repositório inteiro e me dizer, com base no meu perfil (fundador, construo produto, sem experiência prévia em vendas B2B), por onde ir.

- **Recomendação:** 003. O deliverable é software funcionando e a G4 é uma empresa movida a time comercial.
- **O que pesei:** o aviso do README sobre o *baseline* — se eu colar o brief numa IA, sai um score com "win rate do vendedor × win rate do produto". Decidi que a primeira tarefa era descobrir se isso fazia sentido nos dados.

## 2. Exploração — a descoberta que mudou o plano

Antes de qualquer interface, liguei as 4 tabelas e testei cada variável **fora da amostra** (treina até julho, testa agosto–dezembro).

- Win rate entre 60% e 65% em **todo** recorte (vendedor, produto, setor, região, gerente). Qui-quadrado sem significância.
- AUC de 0,48–0,51 para vendedor, produto, conta, setor, receita e preço — cara ou coroa.
- O que tinha sinal: **valor** (500× de diferença entre produtos) e **tempo**. Nenhum deal fechado levou mais de 138 dias, e 81% do Engaging aberto já passou disso.
- Problemas de dados: "GTXPro" em 1.480 linhas, 1.425 deals sem conta, Prospecting sem data, 5 vendedores sem deals.

**Decisão minha:** pedi para a IA explicar "como se eu fosse uma criança" antes de decidir. A analogia da pescaria (tamanho do peixe × tempo da vara na água; varas zumbis) virou a linguagem da ferramenta.

## 3. "Seja fora da caixa, mas sem alucinar"

Não aceitei a primeira leitura e pedi outra rodada mais pesada.

- **A IA corrigiu o próprio erro:** ela tinha afirmado que "deals que passam das 2 primeiras semanas ganham mais". Ao separar por mês do trimestre, o efeito sumiu — era o **calendário** (3º mês do trimestre: 80% de vitória; 1º mês: 49%, em 30 de 30 vendedores).
- **Armadilha de dados:** deals de 2016 pareciam ganhar 82%, porque o dataset só tem fechamentos a partir de mar/2017 — as perdas antigas não existem. Coorte excluída.
- **Teste anti-armadilha dos zumbis:** "nunca fechou depois de 138 dias" poderia ser falta de janela. Não é: a coorte de março teve 305 dias de janela, o deal mais lento fechou em 121 e 137 continuam abertos.
- **ML com tudo junto:** 99,7% de acerto no passado, 50,7% no futuro. Decorou, não aprendeu.
- **Julgamento:** o efeito de fim de trimestre é forte, mas vale para todos os deals ao mesmo tempo, então não muda *qual* deal puxar primeiro. Ficou como contexto, não como peso.

## 4. Planilha relacional

Pedi uma planilha que ligasse tudo por escritório › gerente › vendedor, para eu entender "quem tem o quê". ([`docs/crm_relacional_equipes.xlsx`](../docs/crm_relacional_equipes.xlsx), 54 mil fórmulas, conferida contra o Python.)

Cruzar as tabelas revelou o que a análise por variável não mostrava:
- **Só o escritório Central usa Prospecting**, e todos os Engaging abertos dele são de jul–ago/2017.
- **Nenhuma conta tem dono:** ~15 vendedores de ~3 escritórios mexem em cada conta.

## 5. Segunda rodada com o que eu sabia

- **Receita entre vendedores:** volume explica 46%, ticket/mix 28%, conversão **1%**. O coaching certo não é "feche melhor".
- **O deal-vitrine:** dos 15 GTK 500 abertos (US$ 401 mil), 14 são zumbis. O único vivo — Rosalina Dieter, Betasoloin, 95 dias — virou o primeiro item da demo.
- **Segundo falso sinal:** "primeiro deal do vendedor com a conta ganha mais" (+3,5 pontos) sumiu ao controlar pelo trimestre. De novo o calendário.

## 6. Minhas perguntas de negócio → testes

| Minha pergunta | Teste | Resposta |
|---|---|---|
| Vale prender vendedor X ao produto Y? | Desempenho vendedor×produto se repete entre semestres? | Não (r = −0,006). Especialização é hábito, não talento |
| Carteira de clientes evita duplicidade? | Concentração da receita por conta; deals simultâneos | Ninguém é dono (o maior fica com 25%); 49% dos pares abertos têm 2+ vendedores |
| Escritórios disputam deals? | Pares simultâneos por nível | Sim, em todos os níveis — ⅓ entre escritórios, ⅓ entre gerentes, ⅓ na mesma equipe |
| Existem negócios ressuscitados? | Proxy: nova oportunidade após perda na mesma conta+produto | 4.516 casos; ganham 61,7% (média 61,5%). Perder não queima a conta |
| O que cada um faz bem? | O que se repete entre semestres | Volume (0,95) e ticket (0,71) sim; conversão (0,35) não |

Um achado que mudou o desenho: em **5.149 pares** dois vendedores ganharam o mesmo produto na mesma conta ao mesmo tempo. Se a ferramenta bloqueasse o segundo deal, mataria receita real. Por isso o conflito é um **aviso**, não um bloqueio.

## 7. Conferir contra o case — e cortar escopo

Pedi para a IA cruzar tudo com os requisitos do desafio. Conclusões:
- Risco real: o avaliador achar que o score é "só ordenar por valor". Precisava de prova.
- Risco real: "documento de 40 páginas onde 5 resolveriam". Muita coisa saiu da ferramenta e virou uma linha no README.

## 8. "Me prova com números reais"

Exigi prova antes de construir. A IA montou um backtest com "máquina do tempo": em 4 datas de 2017, reconstruir o pipeline como estava, deixar cada vendedor escolher 10 deals por estratégia e medir a receita dos 90 dias seguintes — usando só dados anteriores a cada data.

| Estratégia | Receita do foco | Foco em zumbis |
|---|---|---|
| Valor × chance pela idade (a nossa) | US$ 2,35 mi | 1% |
| Só por valor | US$ 2,09 mi | 13% |
| "Baseline de IA" (valor × win rates) | US$ 2,09 mi | 12% |
| Aleatório | US$ 0,87 mi | 14% |
| Mais antigos primeiro | US$ 0,55 mi | 53% |

Vendedor a vendedor, mês a mês: melhor que "só valor" em 56 casos, igual em 51, pior em 13 (ganho médio de US$ 3,7 mil por vendedor/mês, IC 95% US$ 2,5–4,8 mil).

E o que **não** dá para provar ficou escrito: o teste mostra que a fila aponta para os deals certos, não que a atenção faz eles fecharem — o CRM não registra atividade.

## 9. "O que não automatizar?" e "vale trocar de desafio?"

- Desenhei a regra **"a ferramenta sugere, o vendedor decide"**: zumbis não são encerrados sozinhos, conflitos não são bloqueados, segunda chance é sugestão, carteira é decisão de gestão. Cada decisão do vendedor fica registrada — é o dado de atividade que falta.
- Score **sem LLM**: precisa ser auditável e dar sempre o mesmo resultado.
- Perguntei se valia trocar de desafio. Conclusão: não — o que diferencia (análise e prova) já estava feito; o que faltava era execução.

## 10. Protótipo → produto

- Pedi um protótipo HTML com os dados reais para validar a UX ([`prototipo-v0.html`](prototipo-v0.html)).
- Testando, apareceu o pior caso: vendedores do Central quase só têm prospects, e a fila deles abria com um deal de US$ 55. Ajuste: quando o Engaging é fraco, os prospects de maior valor vêm primeiro.
- Na construção, o score foi isolado em `solution/app/src/scoring/` com **12 testes que usam os dados reais e conferem os mesmos números da análise**.

## 11. Erros pegos durante a construção

- **Bug na análise, pego pelo app:** o teste cruzado mostrou 489 oportunidades de segunda chance, contra 1.702 na análise. A causa: em pandas, `linha.product` é um método (multiplicação), não a coluna — o filtro "já existe deal aberto nessa conta+produto" nunca funcionou no script. O app estava certo.
- **Ao reescrever os scripts:** pares simultâneos caíram de 18.875 para 16.694 — prospects sem data estavam contando como "abertos ao mesmo tempo".
- **Entrega:** o `.gitignore` do repositório original ignora `submissions/` (e alterar arquivos fora da minha pasta invalida o PR) → uso de `git add -f`. O ambiente da IA não podia fazer push no meu fork → os commits saíram do meu computador, numa pasta conectada.

---

## Resumo: o que foi da IA e o que foi meu

| A IA fez | Eu fiz |
|---|---|
| Ler o repositório, rodar análises, testes estatísticos e backtest | Escolher o desafio e o enquadramento (o que importa para a chefe de RevOps) |
| Propor a lógica valor × tempo e a linguagem do relógio | Exigir explicação simples antes de decidir |
| Construir protótipo, app, testes e scripts | Fazer as perguntas de negócio que geraram os melhores achados |
| Corrigir os próprios erros quando pressionada | Pressionar: "fora da caixa sem alucinar", "me prova com números", "o que não automatizar" |
| | Validar UX, escopo e se a entrega atende o case |
