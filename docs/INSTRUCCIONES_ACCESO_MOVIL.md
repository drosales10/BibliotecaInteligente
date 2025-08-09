# 📱 Instrucciones para Acceso Móvil

## 🎯 **Problema Resuelto**

El error "Backend no disponible" desde tu celular se debe a que el frontend estaba configurado para usar `localhost:8001`, que no funciona desde dispositivos móviles.

## ✅ **Solución Implementada**

### **1. Configuración del Frontend Actualizada**
- **Archivo**: `frontend/src/config/api.js`
- **Cambio**: Ahora detecta automáticamente si se accede desde un dispositivo móvil
- **Resultado**: Usa la IP local de tu computadora (`192.168.100.6:8001`) para dispositivos móviles

### **2. Configuración del Backend Verificada**
- **Estado**: ✅ Funcionando correctamente
- **Host**: `0.0.0.0:8001` (escucha en todas las interfaces)
- **IP Local**: `192.168.100.6:8001`

## 🔧 **Pasos para Configurar el Acceso Móvil**

### **Opción 1: Script Batch (Recomendado)**
1. **Hacer clic derecho** en `configure_firewall_mobile.bat`
2. **Seleccionar** "Ejecutar como administrador"
3. **Confirmar** la ejecución

### **Opción 2: Script PowerShell**
1. **Hacer clic derecho** en `configure_firewall_mobile.ps1`
2. **Seleccionar** "Ejecutar con PowerShell"
3. **Confirmar** la ejecución

### **Opción 3: Manual (Si los scripts no funcionan)**
1. **Abrir PowerShell como administrador**
2. **Ejecutar** estos comandos:

```powershell
# Regla de entrada
netsh advfirewall firewall add rule name="Biblioteca Inteligente Backend - Entrada" dir=in action=allow protocol=TCP localport=8001

# Regla de salida
netsh advfirewall firewall add rule name="Biblioteca Inteligente Backend - Salida" dir=out action=allow protocol=TCP localport=8001
```

## 📱 **Cómo Acceder desde tu Celular**

### **URL de Acceso**
```
http://192.168.100.6:8001
```

### **Verificación de Conexión**
1. **Abrir navegador** en tu celular
2. **Ir a**: `http://192.168.100.6:8001/api/drive/status`
3. **Deberías ver**: Respuesta JSON del backend

## 🚨 **Solución de Problemas**

### **Si sigue apareciendo "Backend no disponible"**

1. **Verificar que el backend esté ejecutándose**:
   ```bash
   netstat -an | findstr :8001
   ```

2. **Verificar conectividad desde tu computadora**:
   ```bash
   curl http://192.168.100.6:8001/api/drive/status
   ```

3. **Verificar firewall**:
   - Asegúrate de haber ejecutado los scripts como administrador
   - Verifica que las reglas se hayan creado correctamente

### **Si el firewall sigue bloqueando**

1. **Desactivar temporalmente el firewall** (solo para pruebas)
2. **Verificar antivirus** que pueda estar bloqueando conexiones
3. **Reiniciar** el servicio de firewall

## 🔒 **Seguridad**

- **Solo dispositivos en tu red WiFi** pueden acceder
- **El puerto 8001** está abierto solo para conexiones locales
- **No expone** tu aplicación a Internet

## 📞 **Soporte**

Si sigues teniendo problemas:
1. Verifica que ambos dispositivos estén en la misma red WiFi
2. Asegúrate de que el backend esté ejecutándose
3. Verifica que no haya otro software bloqueando el puerto 8001
