# Guia de estilos Sabor & Clic

Este guia registra a identidade vermelha, cinza e branca do projeto e orienta a revisão da interface. A fidelidade ao Figma depende do arquivo original, não fornecido nesta entrega.

## Cores

| Uso | HEX | RGB | Orientação |
| --- | --- | --- | --- |
| Marca e ação principal | #d32f2f | 211, 47, 47 | Botões e destaques com texto branco |
| Texto principal | #333333 | 51, 51, 51 | Texto de leitura |
| Texto secundário | #666666 | 102, 102, 102 | Descrições e navegação |
| Fundo | #f8f9fa | 248, 249, 250 | Fundo da página |
| Superfície | #ffffff | 255, 255, 255 | Cartões e formulários |
| Borda | #dddddd | 221, 221, 221 | Separadores, sem depender deles para indicar foco |

## Tipografia e estrutura

Arial, sans-serif. A marca usa peso forte e aproximadamente 24 px no cabeçalho. Corpo de formulários e conteúdo deve priorizar 16 px e espaçamento confortável. Títulos devem seguir h1, h2 e h3 em ordem lógica. Preços e ações recebem destaque sem competir com o nome do prato.

Cartões simples apresentam nome, descrição, preço, disponibilidade e ação. A navegação inferior conserva acesso às telas do perfil. Reservar espaço no fim da página evita que a navegação cubra conteúdo. CSS puro usa Flexbox/Grid, larguras fluidas e media queries. Evitar rolagem horizontal em celular, inclusive nas tabelas e no KDS.

## Componentes e estados

| Componente | Regra |
| --- | --- |
| Botão | Texto que descreve a ação, foco visível e estado desabilitado quando ocupado |
| Campo | label associado, mensagem de erro próxima e preservação dos dados após falha |
| Feedback | Estado de carregamento, confirmação e erro com texto claro e região acessível |
| KDS | Número do pedido, itens, status textual, estimativa e próxima ação permitida |
| Catálogo | Disponibilidade e falta de estoque indicadas por texto, além da cor |
| Reserva | Data, horário, bancada e status visíveis antes da confirmação |

## Contraste calculado

Branco sobre vermelho: 4.98:1. Cinza #333333 sobre branco: 12.63:1. Cinza #666666 sobre branco: 5.74:1. Esses pares superam 4,5:1 para texto normal segundo o cálculo de luminância relativa. A revisão deve verificar os pares efetivamente usados em cada tela e cada estado.

## Roteiro de revisão visual

- Conferir celular a 360 px, tablet e desktop a 1280 px.
- Navegar com Tab e Shift+Tab e acionar botões pelo teclado.
- Conferir zoom de 200%, legibilidade e ausência de conteúdo coberto.
- Confirmar que status não depende somente de cor e que erros têm mensagem textual.
- Comparar tela a tela com o Figma original após o grupo disponibilizá-lo.

Este guia não atesta conformidade integral WCAG. O grupo deve revisar também foco, semântica, nomes acessíveis, ordem de leitura e mensagens dinâmicas.
