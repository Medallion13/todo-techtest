# 🚀 Serverless Todo App - AWS CDK + React

> **Tiempo de desarrollo:** 12+ horas
> **Iteraciones:** Múltiples chats, refactorizaciones significativas
> **Stack:** Python, TypeScript, AWS CDK, Serverless

---

## 📋 Tabla de Contenidos

- [Arquitectura](#arquitectura)
- [Tecnologías](#tecnologías)
- [Estructura del Proyecto](#estructura-del-proyecto)
- [Configuración y Deployment](#configuración-y-deployment)
- [Endpoints API](#endpoints-api)
- [Decisiones Técnicas](#decisiones-técnicas)
- [Problemas Encontrados](#problemas-encontrados)
- [Lecciones Aprendidas](#lecciones-aprendidas)
- [Mejoras Futuras](#mejoras-futuras)

---

## 🏗️ Arquitectura

### **Backend Serverless (AWS)**

```
┌─────────────────────────────────────────────────────┐
│                   CloudFront                         │
│            (Frontend Distribution)                   │
└──────────────────┬──────────────────────────────────┘
                   │
                   ├─► S3 Bucket (Frontend estático)
                   │
┌──────────────────▼──────────────────────────────────┐
│              API Gateway REST                        │
│         (https://.../prod/)                          │
└──────────────────┬──────────────────────────────────┘
                   │
      ┌────────────┼────────────┐
      │            │            │
      ▼            ▼            ▼
┌─────────┐  ┌─────────┐  ┌─────────┐
│ Lambda  │  │ Lambda  │  │ Lambda  │
│ Register│  │  Login  │  │  Tasks  │
└────┬────┘  └────┬────┘  └────┬────┘
     │            │            │
     └────────────┴────────────┘
                  │
          ┌───────▼────────┐
          │   Cognito      │
          │  User Pool     │
          └────────────────┘
                  │
          ┌───────▼────────┐
          │   DynamoDB     │
          │  (TodoTable)   │
          └────────────────┘
```

---

## 🛠️ Tecnologías

### **Backend**
- **Runtime:** Python 3.12
- **Framework:** AWS Lambda Powertools v2.30.2
- **Validation:** Pydantic v2.7.4
- **IaC:** AWS CDK v2.225.0 (Python)
- **Database:** DynamoDB (Single Table Design)
- **Auth:** AWS Cognito User Pool

### **Frontend**
- **Framework:** React 18 + TypeScript
- **Build Tool:** Vite
- **Styling:** Tailwind CSS
- **State:** Context API + localStorage
- **Hosting:** CloudFront + S3

### **AWS Services**
- API Gateway REST API
- Lambda (4 funciones)
- DynamoDB
- Cognito
- S3
- CloudFront
- IAM

---

## 📁 Estructura del Proyecto

```
todo-app/
├── backend/
│   ├── functions/
│   │   ├── auth/
│   │   │   ├── register.py          # POST /auth/register
│   │   │   └── login.py             # POST /auth/login
│   │   └── tasks/
│   │       ├── create.py            # POST /tasks
│   │       └── list.py              # GET /tasks
│   ├── models/
│   │   └── task.py                  # Pydantic models
│   └── shared/
│       └── responses.py             # Response helpers
│
├── infrastructure/
│   ├── app.py                       # CDK app entry point
│   └── stacks/
│       └── todo_stack.py            # Main stack definition
│
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── auth/
│   │   │   │   ├── LoginForm.tsx
│   │   │   │   └── RegisterForm.tsx
│   │   │   └── tasks/
│   │   │       └── TaskList.tsx (pendiente)
│   │   ├── contexts/
│   │   │   └── AuthContext.tsx
│   │   ├── config/
│   │   │   └── api.ts
│   │   ├── App.tsx
│   │   └── main.tsx
│   ├── package.json
│   └── vite.config.ts
│
├── Makefile                         # Build & deploy automation
├── pyproject.toml                   # Python dependencies
└── README.md
```

---

## 🚀 Configuración y Deployment

### **Pre-requisitos**

```bash
# Node.js 22.19.0
node --version

# Python 3.12
python --version

# AWS CLI configurado
aws configure
# O con SSO:
aws sso login --profile todo-app

# CDK CLI
npm install -g aws-cdk
```

### **Setup del Proyecto**

```bash
# 1. Instalar dependencias Python
poetry install

# 2. Instalar dependencias Frontend
cd frontend && npm install && cd ..

# 3. Bootstrap CDK (solo primera vez)
cd infrastructure
AWS_PROFILE=todo-app cdk bootstrap
cd ..
```

### **Build & Deploy**

```bash
# Build Lambda bundle
make build-lambda

# Deploy infraestructura + frontend
make deploy

# Outputs incluyen:
# - API Gateway URL
# - CloudFront Distribution URL
# - Cognito Pool ID y Client ID
```

### **Deployment Manual de API Gateway**

```bash
# Necesario después de cambios en Lambdas
aws apigateway create-deployment \
  --rest-api-id <API_ID> \
  --stage-name prod \
  --description "Manual deployment"
```

---

## 🌐 Endpoints API

**Base URL:** `https://65czwklzp5.execute-api.us-east-1.amazonaws.com/prod/`

### **Auth Endpoints (Públicos)**

#### `POST /auth/register`
```json
// Request
{
  "email": "user@example.com",
  "password": "Password123"
}

// Response (201)
{
  "statusCode": 201,
  "body": {
    "message": "User registered successfully",
    "email": "user@example.com"
  }
}
```

#### `POST /auth/login`
```json
// Request
{
  "email": "user@example.com",
  "password": "Password123"
}

// Response (200)
{
  "statusCode": 200,
  "body": {
    "message": "Login successful",
    "idToken": "eyJ...",
    "accessToken": "eyJ...",
    "refreshToken": "eyJ...",
    "expiresIn": 3600
  }
}
```

### **Task Endpoints (Protegidos - Requieren JWT)**

#### `POST /tasks`
```bash
# Headers requeridos
Authorization: Bearer <idToken>
Content-Type: application/json

# Request
{
  "title": "Mi tarea",
  "description": "Descripción opcional",
  "status": "pending"  // pending | in_progress | done
}

# Response (201)
{
  "statusCode": 201,
  "body": {
    "task_id": "uuid",
    "title": "Mi tarea",
    "status": "pending",
    "created_at": "2025-11-21T...",
    "updated_at": "2025-11-21T..."
  }
}
```

#### `GET /tasks`
```bash
# Headers requeridos
Authorization: Bearer <idToken>

# Response (200)
{
  "statusCode": 200,
  "body": {
    "tasks": [...],
    "count": 5
  }
}
```

---

## 🔑 DynamoDB Schema (Single Table Design)

```python
# Partition Key: PK
# Sort Key: SK

# User's task
PK: "USER#04887478-1031-7090-d522-239b68804dff"
SK: "TASK#uuid-de-la-tarea"

# Permite queries eficientes:
# - Todas las tareas de un usuario: Query PK=USER#{id}
# - Tarea específica: Query PK=USER#{id} AND SK=TASK#{task_id}
```

---

## 🎯 Decisiones Técnicas

### **1. Lambda Proxy Integration**

**Elegido:** Lambda Proxy Integration
**Alternativa:** Non-Proxy con contratos en API Gateway

#### **Pros de Proxy:**
- ✅ Lambda tiene control total de la respuesta
- ✅ Más simple en código (un solo return)
- ✅ Más flexible

#### **Contras encontrados:**
- ❌ Headers CORS requieren configuración explícita
- ❌ API Gateway no extrae headers automáticamente del JSON
- ❌ Debugging más complejo (headers dentro del JSON)

#### **¿Hubiera sido mejor Non-Proxy?**

**SÍ**, probablemente. Con Non-Proxy Integration:

```python
# Lambda solo devuelve el body
return {
    "message": "Login successful",
    "token": "..."
}

# API Gateway agrega automáticamente:
# - statusCode (configurado en integration response)
# - headers CORS (configurados una vez)
# - transformaciones de respuesta
```

**Ventajas:**
- CORS se configura una vez en API Gateway
- Headers consistentes en todas las respuestas
- Contratos OpenAPI/Swagger integrados
- Validación de request/response en API Gateway

**Desventajas:**
- Más complejo de configurar en CDK
- Menos flexible (Lambda no controla statusCode directamente)
- Curva de aprendizaje mayor

**Lección:** Para APIs REST con muchos endpoints, Non-Proxy con contratos definidos en API Gateway es más mantenible a largo plazo.

---

### **2. Single Table Design vs Multi-Table**

**Elegido:** Single Table Design

**Razones:**
- ✅ Queries más eficientes (un solo table scan)
- ✅ Menos overhead de conexiones
- ✅ Patrón recomendado por AWS
- ✅ Escalabilidad

**Trade-off:** Más complejo de entender inicialmente

---

### **3. CloudFront para Frontend**

**Iteraciones:**
1. Intento inicial: S3 directo (HTTP, CORS issues)
2. Segunda iteración: CloudFront simple (cache issues)
3. Versión final: CloudFront con invalidation

**Alternativa considerada:** CloudFront como proxy del API
**Rechazada porque:** Rompe arquitectura desacoplada

---

### **4. Powertools Layer vs Bundle**

**Elegido:** Bundle directo (inicialmente)
**Propuesto:** AWS Managed Layer

**Trade-off:**
- Bundle: 6MB por deploy, más lento
- Layer: 2MB por deploy, más rápido, AWS mantiene actualizaciones

**Pendiente:** Migrar a Layer en futuras iteraciones

---

## 🐛 Problemas Encontrados

### **1. CORS en navegador (12 horas de debugging)**

#### **Síntoma:**
```
Access to fetch at '...' has been blocked by CORS policy:
No 'Access-Control-Allow-Origin' header is present
```

#### **Causa raíz:**
API Gateway con Lambda Proxy Integration no estaba extrayendo los headers del JSON de respuesta de Lambda.

**Lambda devolvía:**
```json
{
  "statusCode": 200,
  "headers": {"Access-Control-Allow-Origin": "*"},
  "body": "..."
}
```

**API Gateway enviaba:**
```
HTTP/1.1 200 OK
Content-Type: application/json

{"statusCode":200,"headers":{...},"body":"..."}
```

**Los headers estaban DENTRO del JSON, no como HTTP headers.**

#### **Diagnóstico:**
- ✅ curl funcionaba (no hace preflight)
- ✅ Postman funcionaba (no hace preflight)
- ❌ Navegador fallaba (hace preflight OPTIONS + valida headers)

#### **Soluciones intentadas:**
1. ❌ Actualizar `responses.py` múltiples veces
2. ❌ Cambiar CORS de API Gateway
3. ❌ Invalidar cache de CloudFront
4. ❌ Agregar headers explícitos en fetch
5. ✅ **CORS extension para desarrollo**

#### **Solución permanente (pendiente):**
```python
# En CDK: Agregar integration_responses y method_responses
register_resource.add_method(
    "POST",
    apigateway.LambdaIntegration(
        register_fn,
        integration_responses=[{
            "statusCode": "200",
            "responseParameters": {
                "method.response.header.Access-Control-Allow-Origin": "'*'"
            }
        }]
    ),
    method_responses=[{
        "statusCode": "200",
        "responseParameters": {
            "method.response.header.Access-Control-Allow-Origin": True
        }
    }]
)
```

---

### **2. API Gateway deployment manual**

#### **Problema:**
CDK no redeploys API Gateway automáticamente cuando cambian solo las integraciones (sin cambios en resources).

#### **Workaround:**
```bash
aws apigateway create-deployment \
  --rest-api-id <API_ID> \
  --stage-name prod
```

#### **Solución propuesta (no implementada):**
```python
# Trigger Lambda que force deployment
triggers.TriggerFunction(..., execute_after=[api])
```

---

### **3. CloudFront cache**

#### **Problema:**
Respuestas viejas cacheadas después de cambios en backend.

#### **Solución:**
```bash
aws cloudfront create-invalidation \
  --distribution-id <DIST_ID> \
  --paths "/*"
```

---

## 📚 Lecciones Aprendidas

### **1. Arquitectura**

- **Lambda Proxy Integration:** Bueno para flexibilidad, malo para CORS consistency
- **Non-Proxy Integration:** Mejor para APIs con muchos endpoints y contratos claros
- **Single Table Design:** Excelente para DynamoDB, pero requiere planning upfront

### **2. Debugging Serverless**

```bash
# Siempre testear en múltiples niveles:
1. curl directo al API Gateway ✅
2. Postman/Insomnia ✅
3. Navegador (con CORS real) ✅
4. CloudWatch Logs ✅
5. API Gateway logs ✅
```

### **3. CORS en Serverless**

**Checklist CORS:**
- [ ] OPTIONS mock integration con headers
- [ ] Lambda responses incluyen headers CORS
- [ ] API Gateway extrae headers del JSON (integration_responses)
- [ ] CloudFront no cachea responses con headers dinámicos
- [ ] Navegador permite el origen (wildcard o específico)

### **4. CDK**

**Pros:**
- ✅ Type-safe (Python con hints)
- ✅ Modular y reutilizable
- ✅ Destroy limpio
- ✅ Best practices built-in

**Contras:**
- ❌ Abstracciones ocultan detalles (ej: default_cors_preflight_options no funciona siempre)
- ❌ Documentación a veces incompleta
- ❌ Debugging de synth errors difícil

---

## 🔮 Mejoras Futuras

### **Alta Prioridad**

1. **Fix CORS permanente**
   - Implementar integration_responses en CDK
   - Remover dependencia de CORS extension
   - Tiempo estimado: 2 horas

2. **Endpoints faltantes**
   - `PUT /tasks/{id}` - Actualizar tarea
   - `DELETE /tasks/{id}` - Eliminar tarea
   - Tiempo estimado: 3 horas

3. **Tests automatizados**
   - Unit tests (Lambdas)
   - Integration tests (API Gateway)
   - E2E tests (Playwright)
   - Tiempo estimado: 8 horas

### **Media Prioridad**

4. **Migrar a Powertools Layer**
   - Reducir tamaño de deploy de 6MB a 2MB
   - Deploys 3x más rápidos
   - Tiempo estimado: 1 hora

5. **CI/CD Pipeline**
   - GitHub Actions
   - Deploy automático a staging/prod
   - Tiempo estimado: 4 horas

6. **Monitoring & Alerting**
   - CloudWatch Dashboards
   - X-Ray tracing
   - SNS alerts
   - Tiempo estimado: 3 horas

### **Baja Prioridad**

7. **Dominio custom**
   - Route53 + ACM Certificate
   - CloudFront con dominio propio
   - Tiempo estimado: 2 horas

8. **Refresh token rotation**
   - Auto-refresh antes de expiry
   - Logout seguro en todos los dispositivos
   - Tiempo estimado: 3 horas

9. **Task sharing**
   - Compartir tareas entre usuarios
   - Permisos granulares
   - Tiempo estimado: 8 horas

---

## 💰 Costos (FREE Tier)

```
Lambda:           1M requests/mes  → $0.00
API Gateway:      1M requests/mes  → $0.00 (12 meses)
DynamoDB:         25GB storage     → $0.00 (permanente)
Cognito:          50K MAU          → $0.00 (permanente)
S3:               5GB storage      → $0.00 (12 meses)
CloudFront:       1TB transfer     → $0.00 (12 meses)

Total mensual: $0.00
```

**Después de FREE tier:**
- Estimado para 1,000 usuarios activos/mes: ~$5-10/mes

---

## 🧪 Testing

### **Backend (curl)**

```bash
# Register
curl -X POST https://API_URL/prod/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"Test1234"}'

# Login
TOKEN=$(curl -s -X POST https://API_URL/prod/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"Test1234"}' \
  | jq -r '.body' | jq -r '.idToken')

# Create task
curl -X POST https://API_URL/prod/tasks \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"title":"Test task","status":"pending"}'

# List tasks
curl -X GET https://API_URL/prod/tasks \
  -H "Authorization: Bearer $TOKEN"
```

### **Frontend (manual)**

Con CORS extension activa:
1. Abrir `http://localhost:5173`
2. Register → Login → Ver tareas

---

## 📝 Comandos Útiles

```bash
# Rebuild Lambda
make build-lambda

# Deploy completo
make deploy

# Ver logs Lambda en tiempo real
aws logs tail /aws/lambda/todo-register --follow

# Invalidar CloudFront cache
aws cloudfront create-invalidation \
  --distribution-id E1W6UNG5J6D2V \
  --paths "/*"

# Ver estado del stack
cd infrastructure && cdk diff

# Destroy todo (cuidado!)
cd infrastructure && cdk destroy
```

---

## 🤝 Contribuir

Este proyecto fue un exercise de aprendizaje intensivo. Áreas donde contribuciones serían valiosas:

1. Fix CORS permanente (CDK integration_responses)
2. Tests automatizados
3. Documentación de API (OpenAPI/Swagger)
4. Optimización de bundle size
5. Mejores prácticas de seguridad

---

## 📜 Licencia

MIT

---

## 🙏 Agradecimientos

- AWS Documentation (aunque a veces confusa)
- Stack Overflow (salvó muchas horas)
- Claude.ai (asistió en debugging y arquitectura)

---

## 📞 Contacto

Para preguntas sobre decisiones de arquitectura o debugging de este proyecto específico, revisar los commits y PRs del repositorio.

---

**Última actualización:** 2025-11-21
**Tiempo total invertido:** ~12 horas
**Estado:** ✅ Funcional con workaround CORS
**Próximo paso:** Implementar fix CORS permanente

> archivo generado con ayuda de claude code
