# Trechos da conversa com a IA

Transcrição dos momentos-chave da sessão no **Claude (Cowork)** em que este case foi construído.
As mensagens do Matheus estão **literais** (com os erros de digitação originais; `[…]` marca trecho omitido).
As respostas da IA estão **resumidas** — a íntegra tinha tabelas e números que já estão no README e em `solution/analysis/results/`.
O foco são os momentos em que eu questionei, redirecionei ou exigi prova.

---

### 1. Ponto de partida

> **Matheus:** […] estou no case tecnico para ia master da g4 business […], eles passaram algo massa que é um case funcional para testar habilidades, com base no que você sabe sobre mim matheus, da uma olhada no que eu vou te passar e me guia primeiro por onde eu poderia seguir e o que nós vemos de possibilidades

**IA:** leu o repositório inteiro, comparou os 4 desafios com meu perfil e recomendou o 003 (deliverable é software; a G4 é uma empresa movida a time comercial). Alertou para o *baseline*: o score "óbvio" com win rate de vendedor × produto é exatamente o que um modelo sozinho entregaria.

> **Matheus:** vamos de 3, vou baixar aqui e já te mando

---

### 2. Primeira análise → pedi para simplificar antes de decidir

**IA:** depois de explorar os dados, trouxe que nenhuma variável óbvia previa quem ganha (AUC ~0,50), que o que tinha sinal era valor e tempo, e que 81% do Engaging eram "zumbis" (> 138 dias).

> **Matheus:** ainda está confuso me explique isso como se eu fosse uma criança, aí fica mais facil de entender e tomarmos decisão

**IA:** explicou com a analogia da pescaria (tamanho do peixe × tempo da vara na água; varas sem peixe = zumbis).
**O que mudou:** essa linguagem virou a da ferramenta — relógio do deal, zumbi, próximo passo.

---

### 3. Não aceitei a primeira leitura

> **Matheus:** sobre a pergunta 1, vamos entender primeiro se não tem algo passando batido, da mais uma analise pra ver se faz sentido ou não isso que você me trouxe e me fala, seja fora da caixa mas sem alucionar

**IA:** rodou uma segunda bateria (censura de dados, calendário, histórico de conta e vendedor, carga, dia da semana, interações, ML com tudo) e **corrigiu o próprio erro**:

> "❌ Onde eu errei: as '2 primeiras semanas' […] Era ilusão. Quando separei por época do ano, o efeito sumiu."

Achou o efeito de fim de trimestre (80% × 49%), a armadilha da coorte de 2016 e confirmou que o limite de 138 dias não é falta de janela. O modelo com tudo junto acertou 99,8% no passado e 50,5% no futuro.

---

### 4. Pedi para ver a estrutura do time

> **Matheus:** preciso que você faca o relacionaemnto exato de todas as planilhas com base no gerente, vendedor e escritorio, pra ficar mais facil de entender qual equipe tem o que, monta essa planilhona que relaciona com exatidão todas as 4 planilhas com valor e me manda pra eu dar uma olhada

**IA:** montou a planilha (`docs/crm_relacional_equipes.xlsx`), conferiu os totais contra o Python e trouxe dois achados que só apareceram cruzando as tabelas: só o escritório Central usa Prospecting, e nenhuma conta tem dono.

> **Matheus:** com isso que você sabe agora, rode a sua analise novamente pra ver se tem algum insight novo

**IA:** receita entre vendedores = volume (46%) + mix (28%), conversão 1%; dos 15 GTK 500 abertos, 14 são zumbis e o único vivo vira o caso-vitrine; ~9 vendedores ativos na mesma conta; padrão estranho do Central. E um segundo falso insight ("primeiro deal com a conta ganha mais") que sumiu ao controlar pelo trimestre.

---

### 5. Minhas perguntas de negócio

> **Matheus:** uma duvida, vale a pena deixar vendedor x para produto y pq vende mais? ou todo mundo vende tudo?
>
> a atribuicao de deals e criar uma carteira de clientes para evitar duplicidade?
>
> tem escritorios diferentes disputando por deals?
>
> tem também negocios qeu foram ressucitados? pq exemplo, não fechou, voltou depois de x tempo pq alguem ressucitou?
>
> como fica também a previsibilidade pro futuro para as acoes, recomendacoes, o que cada um é bom
>
> pense meio fora da caixa pra isso

**IA:** transformou cada pergunta num teste:
- especialização vendedor×produto não se repete entre semestres (r = −0,006) → não prender produto a vendedor;
- ninguém é dono de conta → carteira por **capacidade**, usando o campo empresa-mãe;
- disputa existe em todos os níveis (⅓ entre escritórios, ⅓ entre gerentes, ⅓ na mesma equipe);
- reabertos após perda ganham igual à média → lista "Segunda chance";
- forecast ingênuo errava até +190%; volume e ticket são traços estáveis, conversão não.

E um alerta que mudou o desenho: em milhares de casos **os dois** vendedores ganharam o mesmo produto na mesma conta — bloquear conflito mataria receita.

---

### 6. Conferir contra o case

> **Matheus:** conta nos requisitos dos desafios com o que vc sabe agora e me fala o que vc chega de conclusao

**IA:** tabela requisito × situação. Dois riscos: o score parecer "só ordenar por valor" e excesso de conteúdo ("40 páginas onde 5 resolveriam"). Proposta de corte de escopo.

---

### 7. Exigi prova

> **Matheus:** mas antes me prova com numeros reais que as coisas que vamos sugerir e imlpementar vão resolver o problema da equipe e o que o case pede, pra termos certeza de tudo

**IA:** montou o backtest com "máquina do tempo" (4 datas de 2017, só dados anteriores a cada data): a fila proposta concentrou US$ 2,35 mi contra US$ 0,87 mi do aleatório e US$ 2,09 mi do "só valor"; melhor em 56, igual em 51, pior em 13 comparações pareadas. E listou o que **não** dava para provar (causalidade, conflito, carteira).

---

### 8. Questionei o "não automatizar tudo"

> **Matheus:** lembra que ta falando pra não tentar automatizar tudo, o que ele esta se referindo nisso? o que geraria de valor pros stakeholders essa solucao proposta?

**IA:** definiu a regra "a ferramenta sugere, o vendedor decide", com o dado que justifica cada fronteira (zumbi não é encerrado sozinho porque o CRM não registra atividade; conflito não é bloqueado por causa dos casos em que os dois ganharam), e o valor para vendedor, gerente, RevOps e diretoria.

---

### 9. Questionei a própria escolha

> **Matheus:** de acordo com o case inteiro, acha realmente que com essa solucao vamos passar? ou compensa pegar outro desafio?

**IA:** recomendou ficar no 003 (o diferencial já estava feito; trocar seria recomeçar com as mesmas armadilhas) e listou os riscos reais restantes — execução, excesso de conteúdo, process log.

---

### 10. Validar antes de construir

> **Matheus:** pode, mas antes gera um html do software que você pensou pra eu dar uma olhada na ux como se fosse o real só que direto no html pra eu validar e dai já mete marcha na criacao das coisas

**IA:** protótipo navegável com os dados reais (`process-log/prototipo-v0.html`). No teste, achou o pior caso (vendedores do Central com fila começando num deal de US$ 55) e corrigiu.

> **Matheus:** agora me explique o problema es solucoes que você propos como se eu fosse uma crianca

> **Matheus:** fechou, vamos fazer a versão final, o que precisa?

---

### Nota sobre números

Alguns números destes trechos foram refinados depois, quando a análise virou scripts reproduzíveis (ex.: ML 99,8%/50,5% → 99,7%/50,7%; segunda chance 1.702 → 489 após um bug encontrado pelo teste cruzado com o app). Os números válidos são os de `solution/analysis/results/` e do README.
