# API de Clasificación de Residuos Reciclables - Colombia

## Descripción General

Sistema de clasificación automática de residuos mediante visión por computadora, diseñado específicamente para el esquema de separación de residuos de Colombia. Utiliza modelos de deep learning pre-entrenados (ResNet-50) para identificar objetos en imágenes y proporcionar información contextualizada sobre su disposición correcta según el código de colores nacional.

## Arquitectura Técnica

### Stack Tecnológico

- **Framework Web**: FastAPI 0.104.1
- **Servidor ASGI**: Uvicorn 0.24.0
- **Modelo de ML**: Microsoft ResNet-50 (via Transformers)
- **Deep Learning Framework**: PyTorch 2.0.1
- **Procesamiento de Imágenes**: Pillow 9.5.0
- **Runtime**: Python 3.11

### Infraestructura

- **Containerización**: Docker
- **Orquestación Local**: Docker Compose
- **Target Deployment**: Google Cloud Run
- **Arquitectura**: Stateless REST API
- **Escalabilidad**: Horizontal scaling via Cloud Run

## Características Principales

### 1. Clasificación de Imágenes

- Detección automática de objetos reciclables mediante CNN
- Precisión optimizada para categorías comunes de residuos
- Procesamiento en CPU (device=-1) para compatibilidad con entornos serverless
- Manejo robusto de múltiples formatos de imagen (JPEG, PNG, WebP)

### 2. Sistema de Clasificación Colombiano

Implementa el código de colores establecido por la normativa colombiana:

- **Caneca Blanca**: Residuos aprovechables (plástico, vidrio, metal, papel)
- **Caneca Verde**: Residuos orgánicos biodegradables
- **Caneca Negra**: Residuos no aprovechables

### 3. Endpoints Duales

#### `/clasificar/` (Web Application)
- Diseñado para consumo desde aplicaciones web
- Respuesta en formato JSON estructurado
- Incluye metadatos extendidos de clasificación

#### `/webhook/whatsapp/` (Messaging Platform)
- Optimizado para integración con Kapso/WhatsApp Business API
- Respuesta en texto plano formateado
- Mensaje legible para usuarios finales

## Instalación y Configuración

### Prerrequisitos

```bash
Docker >= 20.10
Docker Compose >= 2.0
```

### Despliegue Local

1. Clonar el repositorio:

```bash
git clone <repository-url>
cd <project-directory>
```

2. Construir la imagen Docker:

```bash
docker-compose build
```

3. Iniciar el servicio:

```bash
docker-compose up
```

La API estará disponible en `http://localhost:8080`

### Despliegue en Google Cloud Run

1. Configurar Google Cloud SDK:

```bash
gcloud auth login
gcloud config set project <project-id>
```

2. Build y push de la imagen:

```bash
gcloud builds submit --tag gcr.io/<project-id>/reciclaje-api
```

3. Deploy en Cloud Run:

```bash
gcloud run deploy reciclaje-api \
  --image gcr.io/<project-id>/reciclaje-api \
  --platform managed \
  --region us-central1 \
  --memory 4Gi \
  --cpu 2 \
  --timeout 300 \
  --allow-unauthenticated
```

## Documentación de API

### Endpoints

#### GET `/`

Health check y metadatos del servicio.

**Response:**
```json
{
  "status": "online",
  "servicio": "API Reciclaje Colombia",
  "version": "2.0",
  "endpoints": {
    "web": "/clasificar/",
    "whatsapp": "/webhook/whatsapp/"
  }
}
```

#### GET `/health`

Verificación de estado del modelo ML.

**Response:**
```json
{
  "status": "healthy",
  "model": "loaded"
}
```

#### POST `/clasificar/`

Clasificación de imagen para aplicaciones web.

**Request:**
- Content-Type: `multipart/form-data`
- Body: `file` (imagen en formato JPEG, PNG, WebP)

**Response Structure:**
```json
{
  "success": true,
  "objeto_detectado": "water bottle",
  "objeto_detectado_espanol": "Botella de agua",
  "confianza": 87.5,
  "nivel_confianza": "alta",
  "emoji_confianza": "✅",
  "sugerencia_foto": null,
  "tipo": "Plástico",
  "caneca": "CANECA BLANCA",
  "categoria": "Aprovechable",
  "consejo": "Enjuaga el envase y aplástalo antes de depositarlo",
  "reciclable": true,
  "materiales_similares": ["Botellas PET", "Envases de champú"],
  "impacto_ambiental": "El plástico tarda entre 100 y 1000 años en degradarse",
  "dato_curioso": "Una botella reciclada ahorra energía para 3 horas de TV",
  "puntos_reciclaje": ["Puntos verdes", "Centros de acopio"]
}
```

**Niveles de Confianza:**
- `alta`: >= 70% (recomendación directa)
- `media`: 40-69% (sugerencia de mejor captura)
- `baja`: < 40% (requiere nueva fotografía)

#### POST `/webhook/whatsapp/`

Endpoint para integración con plataformas de mensajería.

**Request:**
- Idéntico a `/clasificar/`

**Response:**
```json
{
  "message": "DETECCIÓN\nBotella de agua\n\nCANECA BLANCA\nTipo: Plástico...",
  "success": true,
  "data": { /* objeto completo de clasificación */ }
}
```

## Optimizaciones de Rendimiento

### 1. Pre-carga del Modelo

El modelo ResNet-50 se descarga durante la construcción de la imagen Docker (Dockerfile, línea 17), evitando cold starts en producción:

```dockerfile
RUN python -c "from transformers import pipeline; \
    pipeline('image-classification', model='microsoft/resnet-50', device=-1)"
```

### 2. Procesamiento de Imágenes

- Redimensionamiento automático a 800px (máximo) para reducir consumo de memoria
- Conversión a RGB para compatibilidad con el modelo
- Doble estrategia de carga (BytesIO + archivo temporal) para manejar edge cases de Pillow

### 3. Configuración de Recursos

**Límites recomendados (Cloud Run):**
- CPU: 2 vCPUs
- Memoria: 4GB
- Timeout: 300s
- Workers: 1 (evita sobrecarga de memoria)

## Consideraciones de Seguridad

### CORS

Configuración permisiva para desarrollo. **Para producción, restringir orígenes:**

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://yourdomain.com"],
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["Content-Type"],
)
```

### Validación de Input

- Validación de tamaño de archivo (implementar límite máximo)
- Validación de tipo MIME
- Sanitización de nombres de archivo

### Rate Limiting

Implementar rate limiting en producción:

```python
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
```

## Mantenimiento y Monitoreo

### Logs Estructurados

La aplicación utiliza logs descriptivos. Para producción, integrar con Cloud Logging:

```bash
gcloud logging read "resource.type=cloud_run_revision" \
  --limit 50 --format json
```

### Métricas Recomendadas

- Latencia de inferencia (p50, p95, p99)
- Tasa de éxito/error por endpoint
- Distribución de niveles de confianza
- Uso de memoria durante inferencia

### Alertas Sugeridas

- Latencia > 5s en p95
- Tasa de error > 5%
- Uso de memoria > 90%
- Cold start frequency

## Testing

### Test Local

```bash
curl -X POST "http://localhost:8080/clasificar/" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@test_image.jpg"
```

### Test con Python

```python
import requests

url = "http://localhost:8080/clasificar/"
files = {"file": open("test_image.jpg", "rb")}
response = requests.post(url, files=files)
print(response.json())
```

## Limitaciones Conocidas

1. **Modelo Base**: ResNet-50 está entrenado en ImageNet, no específicamente en residuos. La precisión puede variar con objetos poco comunes.

2. **Procesamiento CPU**: El modelo corre en CPU por compatibilidad con Cloud Run. Para mayor throughput, considerar GPU instances.

3. **Idioma**: Las etiquetas del modelo están en inglés. La traducción al español es manual y limitada a objetos comunes.

4. **Contexto Local**: La clasificación por colores es específica de Colombia y puede no aplicar a otras jurisdicciones.

## Roadmap

- [ ] Implementación de modelo fine-tuned en dataset de residuos
- [ ] Soporte multi-idioma automático
- [ ] Cache de resultados con Redis
- [ ] API de batch processing
- [ ] SDK cliente en JavaScript/Python
- [ ] Telemetría con OpenTelemetry
- [ ] Integración con sistemas de gestión de residuos municipales

## Contribución

Este proyecto sigue las convenciones de Python PEP 8. Para contribuir:

1. Fork del repositorio
2. Crear feature branch (`git checkout -b feature/nueva-funcionalidad`)
3. Commit con mensajes descriptivos
4. Push al branch (`git push origin feature/nueva-funcionalidad`)
5. Abrir Pull Request

## Licencia

[Especificar licencia del proyecto]

## Contacto y Soporte

[Información de contacto del mantenedor]

---

**Versión**: 2.0  
**Última actualización**: Diciembre 2024