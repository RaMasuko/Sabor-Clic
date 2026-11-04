# DER nativo brModelo

O arquivo DER_SABOR_CLIC.brM3 é uma proposta editável gerada com as próprias classes Java da distribuição oficial do brModelo. É um arquivo binário nativo, não um SVG ou XML com extensão renomeada. O grupo deve abrir o arquivo no brModelo e revisar o modelo conceitual, as cardinalidades e a disposição visual antes da entrega.

## Origem e escopo

Fonte primária: https://github.com/chcandido/brModelo

Versão do repositório utilizada: 0cbda0225d9fbbff54469e06a99c21fee4e680d5.

A geração parte das 10 tabelas de sql/01_modelo_fisico.sql. Inclui campos como atributos, identifica chaves primárias e opcionalidade e converte as 5 chaves estrangeiras declaradas em relacionamentos. É uma engenharia reversa para revisão, incluindo tabelas técnicas de sessão, tentativas de login e auditoria. Referências polimórficas ou lógicas sem FK declarada não foram apresentadas como relacionamentos físicos. A revisão conceitual deve decidir como representar ou separar essas entidades técnicas e campos de ligação.

A cardinalidade do lado referenciado permite zero ou muitas ocorrências. Cada registro que contém FK obrigatória referencia exatamente um registro pai. Para pedidos, a aplicação exige ao menos um item mesmo que a FK isolada permita pedido vazio. Esta regra deve ser discutida na modelagem conceitual final.

## Validação realizada

O processo criou Editor e DiagramaConceitual oficiais em Java 17 headless, serializou GuardaPadraoBrM com ObjectOutputStream e reabriu o arquivo com ObjectInputStream e GuardaPadraoBrM.getDiagrama, exatamente as classes utilizadas no leitor oficial. O leitor recuperou 10 entidades, 5 relacionamentos, 68 atributos e 172 objetos no total. Uma segunda leitura confirmou que nenhuma ligação possui ponta desconectada. A renderização também usou Diagrama.ExternalPaint do JAR oficial e foi inspecionada. A disposição usa âncoras nas bordas das entidades e nos círculos dos atributos, com orientação voltada à entidade para evitar que as ligações atravessem os rótulos. Os campos foram preservados. Não houve abertura interativa no aplicativo desktop.

SHA256 do JAR oficial usado: 408c836abe1d6e5b0ab836cf3231471333caaa522204c663c679c17a9e9b4264

SHA256 do arquivo nativo: 57c2c01702941f149e59ea52cd4e469420a06de600969a1b91f0d8d5aa210005

O DER_REFERENCIA.pdf continua sendo uma visão resumida e legível das relações centrais. O arquivo nativo contém o detalhamento editável das entidades físicas. A disponibilização deste arquivo não substitui a revisão e explicação pelos integrantes.
