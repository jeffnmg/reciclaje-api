from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import io
import traceback
from transformers import pipeline

# Cargar modelo
print("⏳ Cargando modelo...")
try:
    # Modelo más robusto y rápido
    classifier = pipeline(
        "image-classification", 
        model="microsoft/resnet-50",
        device=-1  # Forzar CPU
    )
    print("✅ Modelo cargado exitosamente")
except Exception as e:
    print(f"❌ ERROR cargando modelo: {e}")
    raise

app = FastAPI(title="♻️ API Reciclaje Colombia")

# CORS para permitir llamadas desde cualquier origen
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def obtener_info_reciclaje_colombia(etiqueta: str):
    """Clasificación según código de colores de Colombia"""
    etiqueta = etiqueta.lower()
    
    if any(w in etiqueta for w in ["bottle", "plastic", "cup", "container", "jug"]):
        return {
            "tipo": "Plástico",
            "caneca": "⚪ CANECA BLANCA",
            "categoria": "Aprovechable",
            "consejo": "Enjuaga el envase y aplástalo antes de depositarlo",
            "reciclable": True,
            "materiales_similares": ["Botellas PET", "Envases de champú", "Bolsas plásticas limpias"],
            "impacto_ambiental": "El plástico tarda entre 100 y 1000 años en degradarse",
            "dato_curioso": "💡 Una botella reciclada ahorra energía para 3 horas de TV",
            "puntos_reciclaje": ["Puntos verdes", "Centros de acopio", "Recicladores de base"]
        }
    
    elif any(w in etiqueta for w in ["glass", "jar", "wine", "beer"]):
        return {
            "tipo": "Vidrio",
            "caneca": "⚪ CANECA BLANCA",
            "categoria": "Aprovechable",
            "consejo": "Retira tapas metálicas, enjuaga bien",
            "reciclable": True,
            "materiales_similares": ["Botellas de vino", "Frascos de alimentos", "Envases de perfume"],
            "impacto_ambiental": "El vidrio es 100% reciclable infinitas veces",
            "dato_curioso": "🌟 Reciclar 1 botella ahorra energía para 20 horas de LED",
            "puntos_reciclaje": ["Contenedores blancos", "Vidrieros locales"]
        }
    
    elif any(w in etiqueta for w in ["can", "tin", "aluminum", "metal"]):
        return {
            "tipo": "Metal/Lata",
            "caneca": "⚪ CANECA BLANCA",
            "categoria": "Aprovechable",
            "consejo": "Aplana las latas para ahorrar espacio",
            "reciclable": True,
            "materiales_similares": ["Latas de bebidas", "Latas de conservas", "Tapas metálicas"],
            "impacto_ambiental": "Reciclar aluminio ahorra 95% de energía",
            "dato_curioso": "♻️ Una lata puede ser lata nueva en 60 días",
            "puntos_reciclaje": ["Chatarreros certificados", "Puntos de acopio"]
        }
    
    elif any(w in etiqueta for w in ["paper", "cardboard", "box", "book"]):
        return {
            "tipo": "Papel/Cartón",
            "caneca": "⚪ CANECA BLANCA",
            "categoria": "Aprovechable",
            "consejo": "Solo si está limpio y seco",
            "reciclable": True,
            "materiales_similares": ["Periódicos", "Cajas de cartón", "Papel de oficina"],
            "impacto_ambiental": "1 tonelada reciclada salva 17 árboles",
            "dato_curioso": "📚 El papel se recicla hasta 7 veces",
            "puntos_reciclaje": ["Cartoneros", "Cooperativas de recicladores"]
        }
    
    elif any(w in etiqueta for w in ["banana", "apple", "orange", "food", "fruit"]):
        return {
            "tipo": "Orgánico",
            "caneca": "🟢 CANECA VERDE",
            "categoria": "Orgánico biodegradable",
            "consejo": "Ideal para compostaje",
            "reciclable": False,
            "materiales_similares": ["Cáscaras de frutas", "Restos de comida", "Residuos de jardín"],
            "impacto_ambiental": "En rellenos genera metano. ¡Compóstalos!",
            "dato_curioso": "🌱 El compostaje reduce 30% residuos del hogar",
            "puntos_reciclaje": ["Composteras comunitarias", "Agricultura urbana"]
        }
    
    else:
        return {
            "tipo": "No identificado",
            "caneca": "⚫ CANECA NEGRA",
            "categoria": "No aprovechable (por precaución)",
            "consejo": "Si tienes dudas, deposítalo en la caneca negra",
            "reciclable": False,
            "materiales_similares": ["Objetos mixtos", "Artículos electrónicos pequeños"],
            "impacto_ambiental": "La clasificación correcta facilita el reciclaje",
            "dato_curioso": "🤔 Consulta con tu operador de aseo local",
            "puntos_reciclaje": ["CAI ambiental", "Línea de atención de aseo"]
        }

@app.get("/")
def home():
    return {
        "status": "online",
        "servicio": "API Reciclaje Colombia",
        "version": "2.0",
        "endpoints": {
            "web": "/clasificar/",
            "whatsapp": "/webhook/whatsapp/"
        }
    }

@app.get("/health")
def health():
    return {"status": "healthy", "model": "loaded"}

@app.post("/clasificar/")
async def clasificar(file: UploadFile = File(...)):
    """Endpoint para web (Lovable)"""
    try:
        # Validar que se recibió un archivo
        if not file:
            raise HTTPException(status_code=400, detail="No se recibió ningún archivo")
        
        # Leer contenido
        print(f"📥 Recibiendo archivo: {file.filename}, tipo: {file.content_type}")
        contents = await file.read()
        print(f"📦 Tamaño del archivo: {len(contents)} bytes")
        
        if len(contents) == 0:
            raise HTTPException(status_code=400, detail="El archivo está vacío")
        
        # Abrir imagen
        try:
            image = Image.open(io.BytesIO(contents))
            print(f"🖼️ Imagen abierta: {image.format}, {image.size}, {image.mode}")
            
            # Convertir a RGB si es necesario
            if image.mode != 'RGB':
                print(f"🔄 Convirtiendo de {image.mode} a RGB")
                image = image.convert('RGB')
                
        except Exception as img_error:
            print(f"❌ Error al abrir imagen: {img_error}")
            raise HTTPException(status_code=400, detail=f"No se pudo procesar la imagen: {str(img_error)}")
        
        # Redimensionar la imagen si es muy grande (evita errores de memoria)
        max_size = 800
        if max(image.size) > max_size:
            print(f"🔄 Redimensionando imagen de {image.size}")
            image.thumbnail((max_size, max_size), Image.Resampling.LANCZOS)
            print(f"✅ Nueva dimensión: {image.size}")
        
        # Clasificar con manejo especial para evitar bug de Pillow
        print("🤖 Clasificando imagen...")
        try:
            # Guardar y recargar la imagen para evitar problemas de formato interno
            img_byte_arr = io.BytesIO()
            image.save(img_byte_arr, format='JPEG', quality=95)
            img_byte_arr.seek(0)
            image_clean = Image.open(img_byte_arr)
            
            resultados = classifier(image_clean)
            print(f"✅ Resultados: {resultados}")
        except Exception as e:
            print(f"⚠️ Método 1 falló, probando alternativa: {e}")
            # Plan B: guardar en archivo temporal
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp:
                image.save(tmp.name, 'JPEG')
                resultados = classifier(tmp.name)
                print(f"✅ Resultados (método alternativo): {resultados}")
        
        top = resultados[0]
        
        confianza_porcentaje = round(top['score'] * 100, 1)
        
        if confianza_porcentaje >= 70:
            nivel_confianza = "alta"
            sugerencia_foto = None
            emoji_confianza = "✅"
        elif confianza_porcentaje >= 40:
            nivel_confianza = "media"
            sugerencia_foto = "💡 Intenta acercar más la cámara"
            emoji_confianza = "⚠️"
        else:
            nivel_confianza = "baja"
            sugerencia_foto = "📸 Toma otra foto más cerca o con mejor luz"
            emoji_confianza = "⚠️"
        
        traducciones = {
            "water bottle": "Botella de agua",
            "coffee mug": "Taza de café",
            "plastic bag": "Bolsa plástica",
            "wine glass": "Copa de vino",
            "beer bottle": "Botella de cerveza",
            "banana": "Banana/Plátano",
            "apple": "Manzana",
            "orange": "Naranja"
        }
        
        objeto_espanol = traducciones.get(top['label'], top['label'])
        info = obtener_info_reciclaje_colombia(top['label'])
        
        print(f"✅ Clasificación exitosa: {objeto_espanol}")
        
        return {
            "success": True,
            "objeto_detectado": top['label'],
            "objeto_detectado_espanol": objeto_espanol,
            "confianza": confianza_porcentaje,
            "nivel_confianza": nivel_confianza,
            "emoji_confianza": emoji_confianza,
            "sugerencia_foto": sugerencia_foto,
            **info
        }
    except HTTPException:
        raise
    except Exception as e:
        error_detail = f"{str(e)}\n\nTraceback:\n{traceback.format_exc()}"
        print(f"❌ ERROR COMPLETO: {error_detail}")
        raise HTTPException(status_code=500, detail=error_detail)

@app.post("/webhook/whatsapp/")
async def whatsapp_webhook(file: UploadFile = File(...)):
    """Endpoint específico para Kapso/WhatsApp - Responde en texto plano"""
    try:
        # Clasificar la imagen
        resultado = await clasificar(file)
        
        if not resultado["success"]:
            return {"message": "❌ No pude procesar la imagen. Intenta de nuevo."}
        
        # Formatear respuesta para WhatsApp (texto bonito)
        emoji_reciclable = "✅" if resultado["reciclable"] else "❌"
        
        mensaje = f"""🔍 *DETECCIÓN*
{resultado['objeto_detectado_espanol']}

{resultado['caneca']}
📦 *Tipo:* {resultado['tipo']}
{emoji_reciclable} {("Reciclable" if resultado['reciclable'] else "No reciclable")}

💬 *¿Cómo depositarlo?*
{resultado['consejo']}

🌍 *Impacto ambiental*
{resultado['impacto_ambiental']}

{resultado['dato_curioso']}

📊 *Confianza:* {resultado['confianza']}% ({resultado['nivel_confianza']})"""
        
        if resultado.get('sugerencia_foto'):
            mensaje += f"\n\n{resultado['sugerencia_foto']}"
        
        return {
            "message": mensaje,
            "success": True,
            "data": resultado
        }
        
    except Exception as e:
        error_msg = f"❌ Error: {str(e)}"
        print(f"ERROR en webhook: {traceback.format_exc()}")
        return {
            "message": error_msg,
            "success": False
        }

if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8080))
    uvicorn.run(app, host="0.0.0.0", port=port)