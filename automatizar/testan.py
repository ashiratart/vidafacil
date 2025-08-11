import os
import pytesseract
from pdf2image import convert_from_path
import re
from openpyxl import Workbook
from openpyxl.styles import Font
from datetime import datetime

# Configurações globais
tesseract_config = '--psm 6'
tesseract_lang = 'por'

# Definições de documentos
DEFINIR_NF = {"Prefeitura", "Nota Fiscal", "Nota de Serviço", "Recibo"}
DEFINIR_BOLETO = {"Linha Digitável", "Código de Barras", "Agência/Código do Beneficiário", "Linha Digitavel", "Agência", "Código do Beneficiário"}


CAMPOS_BOLETO = {
    "Nº do Documento": r"\d+",
    "Vencimento": r"\d{2}/\d{2}/\d{4}",
    "Valor do Documento": r"\d{1,3}(?:\.\d{3})*,\d{2}"
}

CAMPOS_NF = {
    "Número da Nota": r"\d+",
    "Data de Emissão": r"\d{2}/\d{2}/\d{4}(?:\s+\d{2}:\d{2}(?::\d{2})?)?",
    "Data e Hora de Emissão": r"\d{2}/\d{2}/\d{4}(?:\s+\d{2}:\d{2}(?::\d{2})?)?",
    "Valor Total da Nota": r"R?\$?\s*\d{1,3}(?:\.\d{3})*,\d{2}"
}

def renomear_pdf(caminho, tipo):
    """Renomeia o arquivo PDF com base no tipo detectado"""
    pasta, nome_arquivo = os.path.split(caminho)
    nome, ext = os.path.splitext(nome_arquivo)
    
    # Verifica se já não está renomeado
    if not nome.endswith(f"_{tipo}"):
        novo_nome = f"{nome}_{tipo}{ext}"
        novo_caminho = os.path.join(pasta, novo_nome)
        os.rename(caminho, novo_caminho)
        print(f"📂 Arquivo renomeado para: {novo_nome}")
        return novo_caminho
    return caminho

def detectar_tipo_documento(texto_continuo):
    """Detecta se o documento é NF ou Boleto"""
    texto_lower = texto_continuo.lower()
    if any(p.lower() in texto_lower for p in DEFINIR_BOLETO):
        return "BOLETO"
    if any(p.lower() in texto_lower for p in DEFINIR_NF):
        return "NF"
    return "BOLETO"

def extrair_campos(texto_continuo, campos):
    """Extrai os campos específicos do texto usando expressões regulares"""
    encontrados = {}
    for chave, padrao_base in campos.items():
        # Procura primeiro pela chave no texto
        if re.search(re.escape(chave), texto_continuo, re.IGNORECASE):
            padrao = re.search(
                rf"{re.escape(chave)}.*?({padrao_base})", 
                texto_continuo, 
                re.IGNORECASE | re.DOTALL
            )
            encontrados[chave] = padrao.group(1).strip() if padrao else "Não encontrado"
    return encontrados

def processar_pdf(pdf_path):
    """
    Processa um único PDF para classificação e extração de dados
    Retorna um dicionário com os resultados
    """
    print(f"\n🔍 Processando o arquivo: {os.path.basename(pdf_path)}...")
    resultado = {
        'Arquivo Original': os.path.basename(pdf_path),
        'Arquivo Renomeado': '',
        'Tipo': '',
        'Campos': {}
    }
    
    try:
        imagens = convert_from_path(pdf_path)
        tipo_documento = None
        campos_referencia = {}
        
        # Processa apenas as primeiras 2 páginas para performance
        for i, imagem in enumerate(imagens[:2]):
            texto = pytesseract.image_to_string(imagem, config=tesseract_config, lang=tesseract_lang)
            texto_continuo = " ".join(texto.split())
            
            if tipo_documento is None:
                tipo_documento = detectar_tipo_documento(texto_continuo)
                resultado['Tipo'] = tipo_documento
                campos_referencia = CAMPOS_NF if tipo_documento == "NF" else CAMPOS_BOLETO
                
                # Renomeia o arquivo
                novo_caminho = renomear_pdf(pdf_path, tipo_documento)
                resultado['Arquivo Renomeado'] = os.path.basename(novo_caminho)
            
            # Extrai campos apenas na primeira página
            if i == 0:
                campos_encontrados = extrair_campos(texto_continuo, campos_referencia)
                resultado['Campos'].update(campos_encontrados)
        
        print(f"✅ Processado: {resultado['Tipo']}")
        print(f"   Campos encontrados: {', '.join([f'{k}: {v}' for k, v in resultado['Campos'].items()])}")
        return resultado
        
    except Exception as e:
        print(f"❌ Erro ao processar {pdf_path}: {str(e)}")
        resultado['Tipo'] = f"ERRO: {str(e)}"
        return resultado

def exportar_para_excel(resultados, pasta_saida):
    """Exporta os resultados para um arquivo Excel"""
    if not resultados:
        print("⚠️ Nenhum resultado para exportar!")
        return
    
    # Cria o workbook e a planilha
    wb = Workbook()
    ws = wb.active
    ws.title = "Resultados PDF"
    
    # Cabeçalhos
    cabecalhos = ['Arquivo Original', 'Arquivo Renomeado', 'Tipo']
    campos_unicos = set()
    
    for res in resultados:
        campos_unicos.update(res['Campos'].keys())
    
    cabecalhos.extend(sorted(campos_unicos))
    ws.append(cabecalhos)
    
    # Estilo do cabeçalho
    for cell in ws[1]:
        cell.font = Font(bold=True)
    
    # Dados
    for res in resultados:
        linha = [
            res['Arquivo Original'],
            res.get('Arquivo Renomeado', ''),
            res['Tipo']
        ]
        for campo in cabecalhos[3:]:
            linha.append(res['Campos'].get(campo, "Não encontrado"))
        ws.append(linha)
    
    # Ajusta largura das colunas
    for column in ws.columns:
        max_length = 0
        column_letter = column[0].column_letter
        for cell in column:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = (max_length + 2) * 1.2
        ws.column_dimensions[column_letter].width = adjusted_width
    
    # Nome do arquivo com timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    excel_path = os.path.join(pasta_saida, f"resultados_pdfs_{timestamp}.xlsx")
    wb.save(excel_path)
    print(f"\n📊 Resultados exportados para: {excel_path}")
    return excel_path

def processar_pasta(pasta_entrada, pasta_saida=None):
    """Processa todos os PDFs em uma pasta e exporta para Excel"""
    if pasta_saida is None:
        pasta_saida = pasta_entrada
    
    # Verifica se a pasta existe
    if not os.path.exists(pasta_entrada):
        print(f"❌ Pasta de entrada não encontrada: {pasta_entrada}")
        return
    
    if not os.path.exists(pasta_saida):
        os.makedirs(pasta_saida)
    
    # Lista todos os PDFs na pasta
    pdfs = [f for f in os.listdir(pasta_entrada) if f.lower().endswith('.pdf')]
    if not pdfs:
        print(f"❌ Nenhum arquivo PDF encontrado em: {pasta_entrada}")
        return
    
    print(f"\n📂 Encontrados {len(pdfs)} arquivos PDF para processar...")
    
    # Processa cada PDF
    resultados = []
    for pdf in pdfs:
        pdf_path = os.path.join(pasta_entrada, pdf)
        resultados.append(processar_pdf(pdf_path))
    
    excel_path = exportar_para_excel(resultados, pasta_saida)
    return excel_path

if __name__ == "__main__":
    PASTA_PDFS = "automatizar/BOLETOS"  
    PASTA_SAIDA = "automatizar/Exel"  
    
    # Verifica se o Tesseract está instalado
    try:
        pytesseract.get_tesseract_version()
    except:
        print("❌ Tesseract OCR não está instalado ou não está no PATH")
        print("👉 Instale conforme o sistema operacional e adicione ao PATH")
        exit()
    
    # Executa o processamento
    processar_pasta(PASTA_PDFS, PASTA_SAIDA)