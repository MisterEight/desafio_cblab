# Desafio 1 - Modelagem de esquema, coleta e ingestão do JSON

## Descreva o esquema JSON correspondente ao exemplo acima.
O esquema JSON do exemplo acima representa um pedido de restaurante, onde cada pedido é identificado por um `guestCheckId`. O JSON contém informações de cabeçalho, como datas de abertura e fechamento, valores agregados, mesa e garçom. Além disso, inclui um array de `detailLines`, onde cada elemento possui um `guestCheckLineItemId` e, quando é um item do menu, também contém um objeto `menuItem` com atributos como taxa, desconto, taxas de serviço, meios de pagamento ou códigos de erro.

## Descreva a abordagem escolhida em detalhes. Justifique a escolha
A abordagem escolhida para modelar o esquema JSON em tabelas SQL envolve a criação de várias entidades que representam as diferentes partes do pedido. As tabelas são projetadas para refletir as relações entre os dados, como pedidos, itens do menu, descontos e meios de pagamento.

## Desafio 2 — Datalake e respostas de API

## Por que armazenar as respostas das APIs?
Armazenar as respostas das APIs é fundamental para garantir a integridade e a disponibilidade dos dados ao longo do tempo. Isso permite que a equipe de dados realize análises históricas, identifique tendências e tome decisões informadas com base em dados consolidados. Além disso, o armazenamento das respostas facilita a recuperação de informações em caso de falhas na API ou mudanças em sua estrutura, garantindo que os dados estejam sempre acessíveis para consultas e relatórios.

## Como você armazenaria os dados?
A estrutura de pastas para armazenar as respostas da API será organizada de forma a facilitar o acesso e a consulta dos dados. A seguir, apresento uma proposta de estrutura de pastas:

```datalake/
├── getFiscalInvoice/
├── getGuestChecks/
├── getChargeBack/
├── getTransactions/
└── getCashManagementDetails/
```

Cada pasta representa um endpoint da API e pode conter subpastas adicionais para organizar os dados por data e loja. Por exemplo, a pasta `getGuestChecks` pode ser estruturada da seguinte forma:

```datalake/getGuestChecks/ano=2025/mes=07/dia=29/loja=0001```

## Considere que a resposta do endpoint getGuestChecks foi alterada, por exemplo, guestChecks.taxes foi renomeado para guestChecks.taxation. O que isso implicaria?
Essa alteração implicaria na necessidade de atualizar o esquema de dados no data lake e no banco de dados. A mudança no nome do atributo exigiria a modificação dos scripts de ETL para refletir a nova nomenclatura, garantindo que os dados sejam processados corretamente. Além disso, seria necessário revisar as consultas e relatórios que utilizam esse campo para garantir que continuem funcionando conforme esperado. Essa flexibilidade na estrutura do data lake permite que mudanças futuras sejam facilmente incorporadas sem comprometer a integridade dos dados armazenados.