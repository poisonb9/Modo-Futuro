# Lembrete unico: inscricao no programa de afiliados do Mercado Livre.
# Gerado em 14/09/2026 a pedido do Bryan. A tarefa se apaga depois de tocar.
$ErrorActionPreference = 'Continue'
Set-Location 'C:\Users\Administrator\Desktop\Tiktok\YouTube videos para Google Drive\ATUALIZADA\clip_engine'
$texto = @'
Inscricao no programa de afiliados do Mercado Livre — hoje a noite

Onde: www.mercadolivre.com.br/l/afiliados-home  (logado como BRYANEXPAND)
ATENCAO: nao e' /afiliados — esse joga pro login sem explicar.

Por que vale:
- 16% de comissao contra 7% do AliExpress
- pagamento na conta Mercado Pago que voce ja' tem
- entrega em 2 dias, e nao 3 semanas
- o app da API ja' funciona; falta SO' a inscricao

Cuidado: o cookie e' de 24h — curto pro funil video -> perfil -> bio -> loja.

'@
& 'C:\Program Files\Python314\python.exe' -X utf8 lembrete_unico.py --texto $texto --tarefa 'Lembrete_MercadoLivre' 2>&1 | Out-String | Write-Output
