// OAIC Vende · motor del asistente (sin IA, sin servidor).
// Funciones puras: reciben el estado del productor y los datos publicados por el observatorio y devuelven
// mensajes. Toda cifra que se muestra sale de los datos (data/publico/asistente/*.json); nunca se inventa.
// Se usa en el navegador (tablero/asistente.html) y en Node (tests/js/motor.test.mjs).

export const ESTADOS = ["borrador", "lista", "contactando", "negociando", "acordada", "entregada", "cobrada", "cerrada", "cancelada"];
const TRANSICIONES = {
  borrador: ["lista", "cancelada"],
  lista: ["contactando", "cancelada"],
  contactando: ["contactando", "negociando", "cancelada"],
  negociando: ["negociando", "contactando", "acordada", "cancelada"],
  acordada: ["entregada", "cancelada"],
  entregada: ["cobrada"],
  cobrada: ["cerrada"],
  cerrada: [],
  cancelada: [],
};
export const NOMBRE_ESTADO = {
  borrador: "Borrador", lista: "Lista para ofrecer", contactando: "Contactando compradores", negociando: "En negociación",
  acordada: "Trato acordado", entregada: "Entregada", cobrada: "Cobrada", cerrada: "Cerrada", cancelada: "Cancelada",
};
const MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"];
const DIAS = ["domingo", "lunes", "martes", "miercoles", "jueves", "viernes", "sabado"];
const CATEGORIA = {
  mayorista: "Mayorista de frutas y verduras", empacadora: "Empacadora", procesadora: "Procesadora", frio: "Almacén frío",
  abarrotes: "Mayorista de abarrotes", supermercado: "Supermercado", fruteria: "Frutería grande",
};

// ---------------------------------------------------------------- texto
export function normalizar(t) {
  return String(t || "").normalize("NFD").replace(/[̀-ͯ]/g, "").toLowerCase()
    .replace(/(\d),(\d{3})\b/g, "$1$2").replace(/(\d),(\d{1,2})\b/g, "$1.$2")
    .replace(/[¿?¡!,;:()"“”]/g, " ").replace(/\s+/g, " ").trim();
}

function lev(a, b) {
  if (Math.abs(a.length - b.length) > 2) return 9;
  const d = Array.from({ length: a.length + 1 }, (_, i) => [i]);
  for (let j = 1; j <= b.length; j++) d[0][j] = j;
  for (let i = 1; i <= a.length; i++)
    for (let j = 1; j <= b.length; j++)
      d[i][j] = Math.min(d[i - 1][j] + 1, d[i][j - 1] + 1, d[i - 1][j - 1] + (a[i - 1] === b[j - 1] ? 0 : 1));
  return d[a.length][b.length];
}

// ¿Aparece ``clave`` (una o varias palabras) en el texto, tolerando faltas de ortografía en palabras largas?
// Ortografía "fonética" frecuente al escribir rápido: ll/y, v/b, z/c/s, h muda.
const fon = (w) => w.replace(/ll/g, "y").replace(/v/g, "b").replace(/z/g, "s").replace(/c([ei])/g, "s$1").replace(/^h/, "");

function contiene(textoNorm, clave) {
  const k = normalizar(clave);
  if (textoNorm.includes(k)) return true;
  if (fon(textoNorm).includes(fon(k))) return true;
  const palabras = textoNorm.split(" ");
  const ks = k.split(" ");
  if (ks.length === 1) return k.length >= 5 && palabras.some((p) => p.length >= 4 && lev(p, k) <= (k.length >= 8 ? 2 : 1));
  for (let i = 0; i + ks.length <= palabras.length; i++) {
    if (ks.every((w, j) => w === palabras[i + j] || (w.length >= 5 && lev(w, palabras[i + j]) <= 1))) return true;
  }
  return false;
}

export const f2 = (x) => (x == null || Number.isNaN(x) ? "—" : Number(x).toLocaleString("es-MX", { minimumFractionDigits: 2, maximumFractionDigits: 2 }));
export const f0 = (x) => (x == null || Number.isNaN(x) ? "—" : Math.round(Number(x)).toLocaleString("es-MX"));
const pct = (x) => `${x > 0 ? "+" : ""}${Math.round(x)} %`;
const corto = (n) => String(n || "").split(" · ")[0].split(":").slice(-1)[0].trim();

// ---------------------------------------------------------------- números
const UNIDADES = { cero: 0, un: 1, uno: 1, una: 1, dos: 2, tres: 3, cuatro: 4, cinco: 5, seis: 6, siete: 7, ocho: 8, nueve: 9, diez: 10,
  once: 11, doce: 12, trece: 13, catorce: 14, quince: 15, dieciseis: 16, diecisiete: 17, dieciocho: 18, diecinueve: 19, veinte: 20,
  veintiuno: 21, veintidos: 22, veintitres: 23, veinticuatro: 24, veinticinco: 25, treinta: 30, cuarenta: 40, cincuenta: 50, sesenta: 60,
  setenta: 70, ochenta: 80, noventa: 90, cien: 100, ciento: 100, doscientos: 200, doscientas: 200, trescientos: 300, trescientas: 300,
  cuatrocientos: 400, quinientos: 500, quinientas: 500, seiscientos: 600, setecientos: 700, ochocientos: 800, novecientos: 900 };

// Convierte números escritos con letra a cifras: "ocho toneladas y media" → "8.5 toneladas".
export function numerosALetra(textoNorm) {
  const t = textoNorm.split(" ");
  const out = [];
  for (let i = 0; i < t.length; i++) {
    const previoEsNumero = /^\d+(\.\d+)?$/.test(out[out.length - 1] || "");
    if (t[i] in UNIDADES || (t[i] === "mil" && i > 0 && !previoEsNumero)) {
      let total = 0, actual = 0, j = i, usado = false;
      while (j < t.length && (t[j] in UNIDADES || t[j] === "mil" || (t[j] === "y" && t[j + 1] in UNIDADES && t[j + 1] !== "media"))) {
        if (t[j] === "mil") { total += (actual || 1) * 1000; actual = 0; } else if (t[j] !== "y") actual += UNIDADES[t[j]];
        j++; usado = true;
      }
      if (usado && !(j === i + 1 && ["un", "una"].includes(t[i]) && !/^(tonelada|kilo|caja|kg|ton|peso|millar|media)/.test(t[j] || ""))) {
        out.push(String(total + actual)); i = j - 1; continue;
      }
    }
    if (t[i] === "mil" && /^\d+(\.\d+)?$/.test(out[out.length - 1] || "")) { out[out.length - 1] = String(Number(out[out.length - 1]) * 1000); continue; }
    out.push(t[i]);
  }
  return out.join(" ").replace(/(^|\s)(tonelada|kilo) y media\b/g, (_, e, u) => `${e}1.5 ${u}s`).replace(/(\d+(?:\.\d+)?) (toneladas?|tons?|kilos?|kilogramos?|cajas?) y media/g, (_, n, u) => `${Number(n) + 0.5} ${u}`)
    .replace(/(toneladas?|kilos?) y media/g, "$1 .5").replace(/\bmedia tonelada\b/g, "0.5 toneladas").replace(/\bmedio kilo\b/g, "0.5 kilos");
}

function numero(s) { return Number(String(s).replace(/,/g, "")); }

// ---------------------------------------------------------------- extracción
export function extraer(texto, base, hoy = new Date()) {
  const n = numerosALetra(normalizar(texto)).replace(/(\d),(\d{3})\b/g, "$1$2").replace(/(\d),(\d{1,2})\b/g, "$1.$2");
  const r = {};
  for (const f of base.frutas) if (f.sinonimos.some((s) => contiene(n, s))) { r.fruta = f.clave; break; }
  // variedad / calidad
  const mlim = n.match(/(?:#|numero|num|no\.?)\s*([2-5])\b/);
  if (mlim) r.calibre = mlim[1];
  for (const v of ["ataulfo", "manila", "tommy", "haden", "hass", "maradol", "macho", "dominico", "tabasco", "chiapas", "sangria", "rayada", "negra"]) if (contiene(n, v)) r.variedad = v;
  if (/\b(primera|1ra)\b/.test(n)) r.calidad = "primera"; else if (/\b(segunda|2da)\b/.test(n)) r.calidad = "segunda"; else if (/\b(tercera|3ra|rezaga)\b/.test(n)) r.calidad = "tercera";
  // cantidad
  const mq = n.match(/(\d+(?:\.\d+)?)\s*(toneladas?|tons?|tn|t|kilos?|kilogramos?|kgs?|k|cajas?|arpillas?|rejas?|piezas?|millares?)\b/);
  if (mq) {
    const v = numero(mq[1]), u = mq[2];
    if (/^(ton|tn|t$)/.test(u)) r.kg = v * 1000;
    else if (/^(kilo|kg|k$)/.test(u)) r.kg = v;
    else if (/^millar/.test(u)) { r.piezas = v * 1000; }
    else if (/^pieza/.test(u)) r.piezas = v;
    else { r.cajas = v; r.unidad = u.replace(/s$/, ""); }
  }
  const mpk = n.match(/(\d+(?:\.\d+)?)\s*(?:kilos?|kg)\s*(?:cada|por)\s*(?:caja|arpilla|reja)/);
  if (mpk) r.kg_por_caja = numero(mpk[1]);
  // precio
  const mp = n.match(/\$\s*(\d+(?:\.\d+)?)|(\d+(?:\.\d+)?)\s*(?:pesos|mxn|varos)|(?:a|en)\s+(\d+(?:\.\d+)?)\s*(?:el|por)\s*(?:kilo|kg)|(\d+(?:\.\d+)?)\s*(?:el|por|\/)\s*(?:kilo|kg)\b/);
  if (mp) r.precio = numero(mp[1] || mp[2] || mp[3] || mp[4]);
  // municipio
  for (const m of base.municipios) if (contiene(n, m.clave)) { r.municipio = m.nombre; break; }
  // central de destino
  for (const c of base.centrales) {
    const ciudad = normalizar(c.ciudad);
    if (ciudad.length >= 5 && contiene(n, ciudad) && !base.municipios.some((m) => normalizar(m.nombre) === ciudad)) { r.central = c.id; break; }
  }
  if (!r.central && /\b(cdmx|df|iztapalapa|ciudad de mexico)\b/.test(n)) r.central = (base.centrales.find((c) => /Iztapalapa/i.test(c.nombre)) || {}).id;
  if (!r.central && /\b(guadalajara|gdl)\b/.test(n)) r.central = (base.centrales.find((c) => /Mercado de Abasto/i.test(c.nombre) && /Guadalajara/i.test(c.ciudad)) || {}).id;
  // entrega
  if (/\b(en (la )?huerta|en (el )?rancho|a pie de huerta|en parcela|ellos recogen|que (lo |la )?recojan)\b/.test(n)) r.entrega = "huerta";
  else if (/\b(puesto en|llevo|lo llevo|la llevo|entrego en)\b/.test(n)) r.entrega = "destino";
  if (/\b(granel)\b/.test(n)) r.empaque = "granel"; else if (/\b(caja|cajas|arpilla|reja)\b/.test(n)) r.empaque = r.empaque || "caja";
  // fecha
  const f = fecha(n, hoy);
  if (f) r.fecha = f;
  return r;
}

function iso(d) { return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}-${String(d.getDate()).padStart(2, "0")}`; }

export function fecha(n, hoy = new Date()) {
  const d = new Date(hoy.getFullYear(), hoy.getMonth(), hoy.getDate());
  if (/\bpasado manana\b/.test(n)) { d.setDate(d.getDate() + 2); return iso(d); }
  if (/\bmanana\b/.test(n)) { d.setDate(d.getDate() + 1); return iso(d); }
  if (/\b(hoy|ya esta lista|ya lista|de inmediato|inmediato)\b/.test(n)) return iso(d);
  const en = n.match(/en (\d+) dias/); if (en) { d.setDate(d.getDate() + Number(en[1])); return iso(d); }
  if (/(proxima|siguiente|otra) semana/.test(n)) { d.setDate(d.getDate() + 7); return iso(d); }
  for (let k = 0; k < 7; k++) if (new RegExp(`\\b${DIAS[k]}\\b`).test(n)) { let s = (k - d.getDay() + 7) % 7; if (s === 0) s = 7; d.setDate(d.getDate() + s); return iso(d); }
  const dm = n.match(/\b(\d{1,2})\s*(?:\/|-|de)\s*(\d{1,2}|[a-z]+)\b/);
  if (dm) {
    const dia = Number(dm[1]);
    const mes = /^\d+$/.test(dm[2]) ? Number(dm[2]) - 1 : MESES.findIndex((m) => m.startsWith(dm[2].slice(0, 3)));
    if (mes >= 0 && dia >= 1 && dia <= 31) { const x = new Date(d.getFullYear(), mes, dia); if (x < d) x.setFullYear(x.getFullYear() + 1); return iso(x); }
  }
  return null;
}

export function fechaLarga(isoTxt) {
  if (!isoTxt) return "—";
  const [y, m, d] = isoTxt.split("-").map(Number);
  const x = new Date(y, m - 1, d);
  return `${DIAS[x.getDay()].replace("miercoles", "miércoles").replace("sabado", "sábado")} ${d} de ${MESES[m - 1]}`;
}

// ---------------------------------------------------------------- intenciones
const INTENCIONES = [
  ["borrar", ["borrar mis datos", "borra mis datos", "borrar todo", "eliminar mis datos"]],
  ["mis_ofertas", ["mis ofertas", "mis ventas", "mis tratos", "seguimiento", "historial", "como van", "como va mi"]],
  ["temporada", ["mejor mes", "temporada", "que meses", "cuando se paga mejor", "cuando conviene", "en que mes"]],
  ["vender_o_esperar", ["vendo o espero", "vender o esperar", "conviene vender", "conviene esperar", "me espero", "aguantar", "espero o vendo", "vendo ya", "vender ahora"]],
  ["aciertos", ["ha acertado", "acierta", "atinado", "le atina"]],
  ["confianza", ["por que creer", "de donde salen", "confiable", "confiar", "creerle"]],
  ["ingreso_ha", ["hectarea", "por ha", "cuanto deja", "rendimiento"]],
  ["cambiar_cultivo", ["otro cultivo", "sembrar otra", "sembrar otro", "cambiar de cultivo", "que sembrar"]],
  ["riesgo", ["puede bajar", "que tanto baja", "riesgo", "caer el precio"]],
  ["competencia", ["competencia", "otros estados", "de donde llega", "quien mas vende"]],
  ["produccion", ["cuanto se produce", "produccion de mi municipio", "cuanto se cosecha"]],
  ["clima", ["lluvia", "calor", "clima", "temperatura", "huracan", "frio"]],
  ["caro_barato", ["caro", "barato", "comparado con otros anos", "esta alto", "esta bajo"]],
  ["margen", ["cuanto le llega", "intermediario", "coyote", "cuanto me queda", "comision", "acaparador"]],
  ["historia", ["ha cambiado", "ultimos anos", "hace anos"]],
  ["exportar", ["exportar", "exportacion", "extranjero", "estados unidos", "otro pais", "otros paises", "europa", "canada", "japon"]],
  ["demanda", ["demanda", "cuanto compran", "quien necesita", "hay compradores", "se vende bien"]],
  ["compradores", ["comprador", "compradores", "quien compra", "quien me compra", "empacadora", "bodega", "bodeguero", "clientes", "a quien le vendo", "contactos", "telefonos de", "numeros de telefono", "con quien vendo"]],
  ["mejor_central", ["que central", "cual central", "a donde mando", "donde vendo", "a que mercado", "plaza", "donde pagan mas", "donde me pagan", "mejor central"]],
  ["pronostico", ["proximo mes", "siguiente mes", "va a subir", "va a bajar", "pronostico", "que va a pasar", "como va a estar", "el mes que entra"]],
  ["precio_hoy", ["otras centrales", "precio", "a cuanto", "cuanto pagan", "cuanto esta", "cuanto se paga", "cotiza", "como esta el", "como anda", "a como"]],
  ["vender", ["vender", "vendo", "ofrecer", "oferta", "tengo", "cosecha lista", "quiero colocar", "colocar mi", "salir de mi"]],
  ["perfil", ["mi perfil", "soy de", "me llamo", "mi nombre", "mi municipio", "mis cultivos", "siembro", "cultivo "]],
  ["ayuda", ["ayuda", "que puedes", "que haces", "menu", "opciones", "como funciona", "instrucciones"]],
  ["saludo", ["hola", "buenas", "buenos dias", "buen dia", "que tal", "buenas tardes", "buenas noches"]],
  ["gracias", ["gracias", "muy amable", "excelente", "perfecto"]],
];
// Índice de la pregunta del observatorio (preguntas_productor.json) que contesta cada intención.
const PREGUNTA = { pronostico: 0, vender_o_esperar: 1, aciertos: 2, caro_barato: 3, temporada: 4, mejor_central: 5, margen: 7, historia: 8,
  ingreso_ha: 9, cambiar_cultivo: 10, riesgo: 11, competencia: 12, produccion: 13, exportar: 14, clima: 15, confianza: 16 };

export function intencion(texto) {
  const n = numerosALetra(normalizar(texto));
  for (const [nombre, claves] of INTENCIONES) if (claves.some((k) => contiene(n, k))) return nombre;
  return null;
}

// ---------------------------------------------------------------- utilidades de datos
const datosFruta = (D, clave) => (D.frutas || {})[clave];
const nombreFruta = (D, clave) => (D.base.frutas.find((f) => f.clave === clave) || {}).nombre || clave;
const articulo = (D, clave) => (D.base.frutas.find((f) => f.clave === clave) || {}).articulo || clave;
const municipioDe = (D, est) => D.base.municipios.find((m) => m.nombre === (est.perfil || {}).municipio) || D.base.municipios.find((m) => m.nombre === "Tecomán");

function kmA(D, est, idCentral) {
  const m = municipioDe(D, est);
  return m && m.km ? m.km[String(idCentral)] : null;
}

function idCentralPorNombre(D, nombre) {
  const c = corto(nombre).toLowerCase();
  const x = D.base.centrales.find((k) => normalizar(k.ciudad) === normalizar(c)) || D.base.centrales.find((k) => normalizar(k.nombre).includes(normalizar(c)));
  return x ? x.id : null;
}

function respuestaObservatorio(D, fruta, intent) {
  const F = datosFruta(D, fruta);
  const q = F && F.respuestas[PREGUNTA[intent]];
  if (!q) return null;
  return { texto: `**${q.pregunta}**\n${q.respuesta}`, accion: q.accion, fuente: q.fuente, confianza: q.confianza, confianza_pct: q.confianza_pct, actualizado: q.actualizado };
}

function preguntarFruta(D, motivo) {
  return { texto: `¿De qué fruta? ${motivo || ""}`.trim(), botones: D.base.frutas.map((f) => ({ texto: f.nombre, enviar: f.nombre })) };
}

// ---------------------------------------------------------------- respuestas calculadas
export function precioHoy(D, est, fruta) {
  const F = datosFruta(D, fruta);
  if (!F) return { texto: "No tengo datos de esa fruta." };
  const todas = F.hoy || [];
  if (!todas.length) return { texto: `Hoy el SNIIM no publicó cotizaciones de ${articulo(D, fruta)} en las centrales que sigo.` };
  // Variedad principal de Colima (la del pronóstico o la señal); si no hay cotización de ella, todas.
  const principal = ((F.pronostico || [])[0] || (F.senales || [])[0] || {}).variante;
  const familia = principal ? principal.split(" - ")[0].replace(/ # ?\d+$/, "") : null;
  const hoy = familia && todas.some((h) => h.variante.startsWith(familia)) ? todas.filter((h) => h.variante.startsWith(familia)) : todas;
  const unidad = hoy[0].unidad;
  const conKm = hoy.map((h) => ({ ...h, km: kmA(D, est, h.central) }));
  const cercanas = [...conKm].filter((h) => h.km != null).sort((a, b) => a.km - b.km).slice(0, 4);
  const altas = conKm.slice(0, 3);
  const m = municipioDe(D, est);
  const linea = (h) => `• ${corto(h.nombre)} — ${h.variante.replace(" - Primera", "")}: **${f2(h.precio)} ${unidad}**${h.km != null ? ` (~${f0(h.km)} km)` : ""}`;
  let txt = `**${nombreFruta(D, fruta)} · precios del ${fechaLarga(hoy[0].fecha)}** (SNIIM, precio frecuente de mayoreo)\n` +
    `Más cerca de ${m.nombre}:\n${cercanas.map(linea).join("\n")}\nDonde mejor pagan:\n${altas.map(linea).join("\n")}`;
  const s = (F.senales || []).find((x) => /Guadalajara/.test(x.central)) || (F.senales || [])[0];
  if (s) txt += `\nEn ${corto(s.central)} el último mes cerrado (${s.mes}) fue ${f2(s.precio)} ${unidad}: ${s.lectura} (más alto que el ${f0(s.percentil)} % de ${s.meses} meses).`;
  txt += "\nOjo: es precio de mayoreo en la central; en huerta se paga menos (flete, empaque, merma y comisión).";
  return { texto: txt, fuente: "SNIIM · precios del día y señal histórica", confianza: "alta",
    botones: [{ texto: "¿Vendo o espero?", enviar: `vendo o espero ${nombreFruta(D, fruta)}` }, { texto: "Quiero vender", enviar: `quiero vender ${nombreFruta(D, fruta)}` },
      { texto: "¿Qué central me conviene?", enviar: `que central me conviene ${nombreFruta(D, fruta)}` }] };
}

export function mejorCentral(D, est, fruta) {
  const F = datosFruta(D, fruta);
  const obs = respuestaObservatorio(D, fruta, "mejor_central");
  const filas = (F.centrales || []).filter((c) => c.confianza !== "baja" || c.diferencia > 0).map((c) => ({ ...c, km: kmA(D, est, c.id) }))
    .sort((a, b) => (b.diferencia || 0) - (a.diferencia || 0)).slice(0, 5);
  if (!filas.length) return obs || { texto: "No hay comparación de centrales con suficientes meses para esta fruta." };
  const m = municipioDe(D, est);
  const tx = filas.map((c) => `• ${corto(c.central)}: ${c.diferencia >= 0 ? "+" : ""}${f2(c.diferencia)} MXN/kg frente a ${corto(c.referencia)} en ${c.meses} meses ` +
    `(confianza ${c.confianza_pct} %)${c.km != null ? `, ~${f0(c.km)} km desde ${m.nombre}` : ""}` +
    (c.diferencia > 0 ? `. Conviene si el flete extra cuesta menos de ${f2(c.flete_equilibrio)} MXN/kg` : "")).join("\n");
  return { texto: `**¿A qué central mandar ${articulo(D, fruta)}?** Comparación con ${corto(filas[0].referencia)} (misma fruta, mismos meses):\n${tx}` +
      (obs ? `\n\nResumen del observatorio: ${obs.texto.split("\n")[1].split(". ").slice(0, 2).join(". ")}.` : ""),
    fuente: "SNIIM · prueba de diferencia entre centrales", confianza: obs ? obs.confianza : "media", confianza_pct: obs && obs.confianza_pct,
    botones: [{ texto: "Ver compradores", enviar: `compradores de ${nombreFruta(D, fruta)}` }, { texto: "Quiero vender", enviar: `quiero vender ${nombreFruta(D, fruta)}` }] };
}

export function demanda(D, est, fruta) {
  const F = datosFruta(D, fruta);
  const dem = (F && F.demanda) || {};
  const partes = Object.entries(dem).map(([e, c]) => `• ${e}: ${f0(c.mayorista || 0)} mayoristas, ${f0(c.empacadora || 0)} empacadoras, ${f0(c.supermercado || 0)} supermercados grandes`);
  const temp = (F.temporada || []).slice().sort((a, b) => b.indice - a.indice);
  let txt = `**¿Hay demanda para ${articulo(D, fruta)}?**\nNadie publica cuánto compra cada central, así que lo veo con tres señales:\n` +
    `1) Empresas que compran fruta (DENUE, INEGI):\n${partes.join("\n")}`;
  if (temp.length) txt += `\n2) Temporada en ${corto(temp[0].central)}: se paga mejor en ${MESES[temp[0].mes - 1]} y ${MESES[temp[1].mes - 1]}, peor en ${MESES[temp[temp.length - 1].mes - 1]} (confianza ${f0(temp[0].confianza_pct)} %).`;
  const s = (F.senales || [])[0];
  if (s) txt += `\n3) Precio frente a su historia: ${s.lectura} en ${corto(s.central)}.`;
  const e = F.exportacion || {};
  if (e.disponible) txt += `\nAdemás, México exportó ${articulo(D, fruta)} a ${e.paises_destino} países en ${e.anio}.`;
  return { texto: txt, fuente: "DENUE (INEGI) · SNIIM · UN Comtrade", confianza: "media",
    botones: [{ texto: "Ver compradores", enviar: `compradores de ${nombreFruta(D, fruta)}` }, { texto: "¿Puedo exportar?", enviar: `exportar ${nombreFruta(D, fruta)}` }] };
}

// Precio sugerido para una oferta: referencias reales, nunca una cifra sin fuente.
export function sugerirPrecio(D, est, oferta) {
  const F = datosFruta(D, oferta.fruta);
  if (!F) return null;
  const hoy = F.hoy || [];
  const unidad = hoy.length ? hoy[0].unidad : "MXN/kg";
  const filtrar = (h) => !oferta.calibre || h.variante.includes(`# ${oferta.calibre}`);
  let destino = oferta.central ? hoy.filter((h) => h.central === String(oferta.central) && filtrar(h)) : [];
  if (!destino.length) {
    const cerca = hoy.filter(filtrar).map((h) => ({ ...h, km: kmA(D, est, h.central) })).filter((h) => h.km != null).sort((a, b) => a.km - b.km);
    destino = cerca.slice(0, 1);
  }
  const ref = destino[0];
  if (!ref) return null;
  const pron = (F.pronostico || []).find((p) => p.horizonte === 1);
  const parts = (F.margen || []).filter((m) => m.participacion_pct != null).map((m) => m.participacion_pct);
  const pmin = parts.length ? Math.min(...parts) : null, pmax = parts.length ? Math.max(...parts) : null;
  const huerta = parts.length ? [ref.precio * pmin / 100, ref.precio * pmax / 100] : null;
  const ultimoMargen = (F.margen || []).slice().sort((a, b) => b.anio - a.anio)[0];
  return { unidad, central: ref.nombre, central_id: ref.central, variante: ref.variante, fecha: ref.fecha, precio_central: ref.precio, km: kmA(D, est, ref.central),
    pronostico: pron ? { mes: pron.mes, precio: pron.precio, min: pron.min80, max: pron.max80, central: pron.central } : null,
    huerta, participacion: parts.length ? [pmin, pmax] : null, margen_anio: ultimoMargen && ultimoMargen.anio,
    precio_rural: ultimoMargen && ultimoMargen.productor };
}

export function textoPrecioSugerido(D, est, oferta, s) {
  if (!s) return "No encontré cotización de hoy para calcular un precio; puede poner el suyo.";
  let t = `**Precio de referencia (${fechaLarga(s.fecha)})**\n• En ${corto(s.central)} (${s.variante.replace(" - Primera", "")}): **${f2(s.precio_central)} ${s.unidad}** de mayoreo${s.km ? `, a ~${f0(s.km)} km` : ""}.`;
  if (s.pronostico) t += `\n• Pronóstico para ${s.pronostico.mes} en ${corto(s.pronostico.central)}: ${f2(s.pronostico.precio)} (rango probable ${f2(s.pronostico.min)}–${f2(s.pronostico.max)}).`;
  if (s.huerta) t += `\n• Si lo venden **en huerta**, al productor de Colima le ha llegado entre el ${f0(s.participacion[0])} % y el ${f0(s.participacion[1])} % del precio de mayoreo (SIAP vs SNIIM): hoy equivaldría a **${f2(s.huerta[0])}–${f2(s.huerta[1])} ${s.unidad}**.`;
  t += oferta.entrega === "destino" ? `\nComo usted entrega en la central, pida cerca de ${f2(s.precio_central)} y descuente su flete y merma.` :
    "\nPida en la parte alta del rango en huerta si su fruta es de primera; el comprador paga flete y empaque.";
  return t;
}

// ---------------------------------------------------------------- compradores
export function compradoresSugeridos(D, est, oferta, n = 8) {
  const lista = (D.compradores || {}).empresas || [];
  const m = municipioDe(D, est);
  const sin = (D.base.frutas.find((f) => f.clave === oferta.fruta) || { sinonimos: [] }).sinonimos.map(normalizar);
  const previos = {};
  for (const o of est.ofertas || []) for (const c of o.contactos || []) previos[c.comprador_id] = c;
  const destino = oferta.central ? D.base.centrales.find((c) => c.id === String(oferta.central)) : null;
  const puntos = lista.filter((x) => x.tel || x.correo).map((x) => {
    let p = { mayorista: 30, empacadora: 28, procesadora: 18, frio: 10, supermercado: 14, abarrotes: 10, fruteria: 8 }[x.cat] || 0;
    const nom = normalizar(`${x.nombre} ${x.razon || ""}`);
    if (sin.some((s) => s.length >= 4 && nom.includes(s))) p += 25;
    if (/fruta|frut|citric|abarrot|agro|export|empaque|hortaliz/.test(nom)) p += 8;
    if (x.central) p += 12;
    if (/51 a|101 a|251/.test(x.personal || "")) p += 8; else if (/31 a|11 a/.test(x.personal || "")) p += 5;
    const km = m && x.lat ? kmLinea(m.lat, m.lon, x.lat, x.lon) * 1.3 : null;
    if (destino && x.lat) { const kd = kmLinea(destino.lat, destino.lon, x.lat, x.lon); if (kd < 25) p += 20; }
    else if (km != null) p += km < 60 ? 18 : km < 250 ? 10 : km < 600 ? 4 : 0;
    if (x.estado === "Colima" && ["limon", "coco", "papaya", "platano", "tamarindo"].includes(oferta.fruta) && x.cat === "empacadora") p += 10;
    const prev = previos[x.id];
    if (prev && prev.respuesta === "no_interesa") p -= 40;
    if (prev && ["interesado", "contraoferta", "muestra"].includes(prev.respuesta)) p += 15;
    if (x.tel) p += 4;
    return { ...x, puntos: p, km: km != null ? Math.round(km) : null, previo: prev || null };
  });
  return puntos.sort((a, b) => b.puntos - a.puntos).slice(0, n);
}

function kmLinea(a1, o1, a2, o2) {
  const r = (x) => x * Math.PI / 180;
  const a = Math.sin(r(a2 - a1) / 2) ** 2 + Math.cos(r(a1)) * Math.cos(r(a2)) * Math.sin(r(o2 - o1) / 2) ** 2;
  return 6371 * 2 * Math.asin(Math.sqrt(a));
}

export function categoria(c) { return CATEGORIA[c] || c; }

// ---------------------------------------------------------------- mensajes de contacto
export function mensajeOferta(D, est, oferta, comprador) {
  const p = est.perfil || {};
  const cant = oferta.kg ? (oferta.kg >= 1000 ? `${f2(oferta.kg / 1000).replace(/\.00$/, "")} toneladas` : `${f0(oferta.kg)} kg`) : oferta.piezas ? `${f0(oferta.piezas)} piezas` : "";
  const fruta = nombreFruta(D, oferta.fruta).toLowerCase() + (oferta.calibre ? ` #${oferta.calibre}` : "") + (oferta.variedad ? ` ${oferta.variedad}` : "");
  return `Buen día${comprador && comprador.nombre ? `, ${comprador.nombre}` : ""}. ${p.nombre ? `Soy ${p.nombre}, productor` : "Soy productor"} de ${oferta.municipio || p.municipio || "Colima"}, Colima. ` +
    `Ofrezco ${cant} de ${fruta}${oferta.calidad ? ` de ${oferta.calidad}` : ""}, disponible el ${fechaLarga(oferta.fecha)}, ` +
    `${oferta.entrega === "destino" ? "puesto en su bodega" : "para recoger en huerta"}${oferta.empaque ? `, ${oferta.empaque}` : ""}. ` +
    (oferta.precio ? `Precio: $${f2(oferta.precio)} por ${oferta.piezas ? "pieza" : "kg"}. ` : "Acepto propuesta de precio. ") +
    "¿Le interesa? Puedo mandar fotos de la fruta.";
}

export function enlaceWhatsApp(tel, texto) { return `https://wa.me/52${tel}?text=${encodeURIComponent(texto)}`; }
export function enlaceCorreo(correo, asunto, texto) { return `mailto:${correo}?subject=${encodeURIComponent(asunto)}&body=${encodeURIComponent(texto)}`; }
export function enlaceTelefono(tel) { return `tel:+52${tel}`; }

// ---------------------------------------------------------------- ofertas y estados
export function nuevaOferta(datos, ahora = new Date()) {
  return { id: `of-${ahora.getTime().toString(36)}`, creada: ahora.toISOString(), estado: "borrador", historial: [{ estado: "borrador", fecha: ahora.toISOString(), motivo: "creada" }],
    contactos: [], ...datos };
}

export function cambiarEstado(oferta, nuevo, motivo = "", ahora = new Date()) {
  if (!(TRANSICIONES[oferta.estado] || []).includes(nuevo)) throw new Error(`No se puede pasar de ${oferta.estado} a ${nuevo}`);
  return { ...oferta, estado: nuevo, historial: [...oferta.historial, { estado: nuevo, fecha: ahora.toISOString(), motivo }] };
}

export function evaluarPropuesta(D, est, oferta, precio) {
  const s = sugerirPrecio(D, est, oferta);
  if (!s || !precio) return { texto: "Registré la propuesta." };
  const ref = oferta.entrega === "destino" ? s.precio_central : (s.huerta ? (s.huerta[0] + s.huerta[1]) / 2 : null);
  let t = `Le ofrecen **$${f2(precio)} ${s.unidad}**.`;
  if (oferta.entrega === "destino") {
    const dif = (precio / s.precio_central - 1) * 100;
    t += ` En ${corto(s.central)} hoy se paga ${f2(s.precio_central)} de mayoreo (${pct(dif)}).`;
  } else if (s.huerta) {
    t += ` En huerta, la referencia es ${f2(s.huerta[0])}–${f2(s.huerta[1])} (lo que históricamente le llega al productor de Colima del precio de ${corto(s.central)}).`;
    t += precio < s.huerta[0] ? " **Está por debajo de lo normal**: pida más o busque otro comprador." : precio > s.huerta[1] ? " **Está por arriba de lo normal**: es buena oferta." : " Está dentro de lo normal.";
  }
  if (oferta.precio) t += ` Usted pidió $${f2(oferta.precio)}.`;
  const mejor = (datosFruta(D, oferta.fruta).centrales || []).filter((c) => c.diferencia > 0 && c.confianza === "alta").sort((a, b) => b.diferencia - a.diferencia)[0];
  if (mejor) t += ` Alternativa: ${corto(mejor.central)} paga en promedio +${f2(mejor.diferencia)} MXN/kg sobre ${corto(mejor.referencia)}; le conviene si el flete extra cuesta menos.`;
  return { texto: t, referencia: ref };
}

export function resumenOferta(D, o) {
  const cant = o.kg ? (o.kg >= 1000 ? `${f2(o.kg / 1000).replace(/\.00$/, "")} t` : `${f0(o.kg)} kg`) : o.piezas ? `${f0(o.piezas)} piezas` : "cantidad por definir";
  return `${nombreFruta(D, o.fruta)}${o.calibre ? ` #${o.calibre}` : ""}${o.variedad ? ` ${o.variedad}` : ""} · ${cant} · ${fechaLarga(o.fecha)} · ${o.municipio || ""} · ` +
    `${o.entrega === "destino" ? "puesto en destino" : o.entrega === "huerta" ? "en huerta" : "entrega por definir"}${o.precio ? ` · $${f2(o.precio)}/${o.piezas ? "pieza" : "kg"}` : ""}`;
}

// ---------------------------------------------------------------- diálogo
const PASOS = ["fruta", "cantidad", "fecha", "municipio", "entrega", "precio", "confirmar"];

function siguientePaso(b) {
  if (!b.fruta) return "fruta";
  if (!b.kg && !b.piezas && !b.cajas) return "cantidad";
  if (b.cajas && !b.kg_por_caja && !b.kg) return "kg_por_caja";
  if (!b.fecha) return "fecha";
  if (!b.municipio) return "municipio";
  if (!b.entrega) return "entrega";
  if (b.precio === undefined) return "precio";
  return "confirmar";
}

function pedir(D, est, paso) {
  const b = est.flujo.borrador;
  const F = nombreFruta(D, b.fruta);
  switch (paso) {
    case "fruta": return preguntarFruta(D, "Dígame qué quiere vender.");
    case "cantidad": return { texto: `¿Cuánto ${F.toLowerCase()} tiene? Puede decir "8 toneladas", "500 kilos" o "200 cajas".`,
      botones: ["1 tonelada", "5 toneladas", "10 toneladas", "20 toneladas"].map((x) => ({ texto: x, enviar: x })) };
    case "kg_por_caja": return { texto: `¿Cuántos kilos trae cada ${b.unidad || "caja"}?`, botones: ["10 kilos", "15 kilos", "20 kilos", "25 kilos"].map((x) => ({ texto: x, enviar: `${x} cada ${b.unidad || "caja"}` })) };
    case "fecha": return { texto: "¿Cuándo está lista para entregar?", botones: ["Hoy", "Mañana", "Próxima semana", "En 15 días"].map((x) => ({ texto: x, enviar: x })) };
    case "municipio": return { texto: "¿En qué municipio está la huerta?", botones: D.base.municipios.map((m) => ({ texto: m.nombre, enviar: m.nombre })) };
    case "entrega": return { texto: "¿Cómo la entrega?", botones: [{ texto: "La recogen en huerta", enviar: "en huerta" }, { texto: "Yo la llevo a la central", enviar: "puesto en la central" }] };
    case "precio": {
      const s = sugerirPrecio(D, est, b);
      est.flujo.sugerido = s;
      return { texto: `${textoPrecioSugerido(D, est, b, s)}\n\n¿Qué precio quiere pedir por ${b.piezas ? "pieza" : "kilo"}? Escriba la cifra (por ejemplo "18 pesos") o deje que el comprador proponga.`,
        botones: [...(s && s.huerta && b.entrega !== "destino" ? [{ texto: `$${f2(s.huerta[1])}`, enviar: `${s.huerta[1].toFixed(2)} pesos` }] : []),
          ...(s ? [{ texto: `$${f2(s.precio_central)}`, enviar: `${s.precio_central.toFixed(2)} pesos` }] : []), { texto: "Que propongan ellos", enviar: "que propongan" }] };
    }
    case "confirmar": return { texto: `Así queda su oferta:\n**${resumenOferta(D, b)}**\n¿La guardo y busco compradores?`,
      botones: [{ texto: "Sí, guardar", enviar: "si" }, { texto: "Cambiar algo", enviar: "cambiar" }, { texto: "Cancelar", enviar: "cancelar" }] };
    default: return { texto: "" };
  }
}

function flujoOferta(D, est, texto, ex, ahora) {
  const b = est.flujo.borrador;
  const n = normalizar(texto);
  const paso = est.flujo.paso;
  if (/^(cancelar|cancela|ya no|olvidalo)\b/.test(n)) { est.flujo = null; return [{ texto: "Listo, cancelé la oferta. ¿En qué más le ayudo?", botones: menu(D, est) }]; }
  if (paso === "confirmar") {
    if (/^(si|sí|ok|va|dale|claro|guardar|correcto|de acuerdo|si guardar)/.test(n)) {
      let o = nuevaOferta(b, ahora);
      o = cambiarEstado(o, "lista", "confirmada por el productor", ahora);
      est.ofertas = [...(est.ofertas || []), o];
      est.flujo = null;
      est.oferta_activa = o.id;
      return [{ texto: `Guardé su oferta (**${NOMBRE_ESTADO[o.estado]}**). Estos compradores pueden interesarse:`, tarjetas: { tipo: "compradores", oferta: o.id, lista: compradoresSugeridos(D, est, o) },
        botones: [{ texto: "Ver ficha de oferta", accion: { tipo: "documento", documento: "ficha", oferta: o.id } }, { texto: "Más compradores", enviar: "mas compradores" }] }];
    }
    if (/cambiar|corregir|no\b/.test(n)) { est.flujo.paso = "cambiar"; return [{ texto: "¿Qué quiere cambiar?", botones: ["Cantidad", "Fecha", "Municipio", "Entrega", "Precio"].map((x) => ({ texto: x, enviar: `cambiar ${x.toLowerCase()}` })) }]; }
  }
  if (paso === "cambiar") {
    const campo = { cantidad: "cantidad", fecha: "fecha", municipio: "municipio", entrega: "entrega", precio: "precio" }[n.replace("cambiar ", "").trim()];
    if (campo) {
      if (campo === "cantidad") { delete b.kg; delete b.cajas; delete b.piezas; delete b.kg_por_caja; } else if (campo === "precio") delete b.precio; else delete b[campo];
      est.flujo.paso = campo === "cantidad" ? "cantidad" : campo;
      return [pedir(D, est, est.flujo.paso)];
    }
  }
  // completa los campos con lo que se entienda del mensaje
  for (const k of ["fruta", "kg", "cajas", "unidad", "kg_por_caja", "piezas", "fecha", "municipio", "entrega", "empaque", "calibre", "variedad", "calidad", "central"]) if (ex[k] !== undefined && (b[k] === undefined || paso === k || k === "kg_por_caja")) b[k] = ex[k];
  if (paso === "fecha" && !b.fecha && /15 dias|quince/.test(n)) { const d = new Date(ahora); d.setDate(d.getDate() + 15); b.fecha = iso(d); }
  if (paso === "entrega" && !b.entrega) { if (/central|llevo|destino|puesto/.test(n)) b.entrega = "destino"; else if (/huerta|recog|rancho/.test(n)) b.entrega = "huerta"; }
  if (paso === "precio" && b.precio === undefined) {
    if (/propon|ellos|no se|no sé|sin precio|que ofrezcan/.test(n)) b.precio = null;
    else { const m = n.match(/(\d+(?:\.\d+)?)/); if (m) b.precio = Number(m[1]); }
  }
  if (paso === "cantidad" && !b.kg && !b.cajas && !b.piezas) { const m = n.match(/^(\d+(?:\.\d+)?)$/); if (m) b.kg = Number(m[1]) >= 50 ? Number(m[1]) : Number(m[1]) * 1000; }
  if (b.cajas && b.kg_por_caja && !b.kg) b.kg = b.cajas * b.kg_por_caja;
  const sig = siguientePaso(b);
  if (sig === paso && paso !== "confirmar") return [{ texto: "No le entendí bien." }, pedir(D, est, sig)];
  est.flujo.paso = sig;
  return [pedir(D, est, sig)];
}

export function menu(D, est) {
  const f = est.fruta ? nombreFruta(D, est.fruta) : "limón";
  return [{ texto: `Precio del ${f.toLowerCase()} hoy`, enviar: `precio ${f}` }, { texto: "¿Vendo o espero?", enviar: `vendo o espero ${f}` },
    { texto: "Quiero vender", enviar: "quiero vender" }, { texto: "Compradores", enviar: `compradores ${f}` }, { texto: "Mis ofertas", enviar: "mis ofertas" }];
}

function saludo(D, est) {
  const p = est.perfil || {};
  const al = (D.base.alertas || []).filter((a) => !p.cultivos || !p.cultivos.length || p.cultivos.some((c) => normalizar(a.fruta).startsWith(normalizar(nombreFruta(D, c)).slice(0, 4))));
  let t = `¡Hola${p.nombre ? `, ${p.nombre}` : ""}! Soy el asistente de venta del Observatorio. Le digo precios de hoy, a qué central conviene mandar, quién compra (con teléfono) y le ayudo a ofrecer y vender su cosecha.`;
  if (al.length) t += `\n\nAlertas de hoy:\n${al.slice(0, 3).map((a) => `• ${a.titulo}`).join("\n")}`;
  if (!p.municipio) t += "\n\nPara darle distancias reales, dígame de qué municipio es (por ejemplo: \"soy de Tecomán\").";
  return { texto: t, botones: menu(D, est) };
}

function ayuda(D, est) {
  return { texto: "Puede preguntarme con sus palabras, por ejemplo:\n• \"¿A cuánto está el limón?\"\n• \"¿Vendo o espero la papaya?\"\n• \"¿A qué central mando mi plátano?\"\n" +
    "• \"Tengo 8 toneladas de limón para el lunes en Tecomán\"\n• \"¿Quién compra coco?\"\n• \"¿Puedo exportar aguacate?\"\n• \"Mis ofertas\"\n" +
    "Todo lo que me dice se guarda **solo en este teléfono**; el observatorio no recibe sus datos.", botones: menu(D, est) };
}

function perfil(D, est, texto, ex) {
  const p = { ...(est.perfil || {}) };
  const n = normalizar(texto);
  const nom = texto.match(/(?:me llamo|mi nombre es|soy)\s+([A-ZÁÉÍÓÚÑ][a-záéíóúñ]+(?:\s+[A-ZÁÉÍÓÚÑ][a-záéíóúñ]+)?)/);
  if (nom && !D.base.municipios.some((m) => normalizar(m.nombre) === normalizar(nom[1]))) p.nombre = nom[1];
  if (ex.municipio) p.municipio = ex.municipio;
  const cultivos = D.base.frutas.filter((f) => f.sinonimos.some((s) => contiene(n, s))).map((f) => f.clave);
  if (cultivos.length) p.cultivos = [...new Set([...(p.cultivos || []), ...cultivos])];
  est.perfil = p;
  return { texto: `Anotado${p.nombre ? `, ${p.nombre}` : ""}. ${p.municipio ? `Municipio: ${p.municipio}. ` : ""}${p.cultivos && p.cultivos.length ? `Cultivos: ${p.cultivos.map((c) => nombreFruta(D, c)).join(", ")}.` : ""}`.trim(),
    botones: menu(D, est) };
}

export function misOfertas(D, est) {
  const os = (est.ofertas || []).slice().reverse();
  if (!os.length) return { texto: "Todavía no tiene ofertas. Dígame qué quiere vender, por ejemplo \"tengo 5 toneladas de papaya\".", botones: [{ texto: "Quiero vender", enviar: "quiero vender" }] };
  return { texto: `Tiene ${os.length} oferta${os.length > 1 ? "s" : ""}:`, tarjetas: { tipo: "ofertas", lista: os.map((o) => o.id) } };
}

// Punto de entrada: texto del productor → mensajes. Modifica ``est`` (memoria del productor).
export function responder(D, est, texto, ahora = new Date()) {
  est.ofertas = est.ofertas || [];
  const ex = extraer(texto, D.base, ahora);
  const n = normalizar(texto);
  if (est.flujo && est.flujo.tipo === "oferta") {
    const it = intencion(texto);
    const cambia = ["precio_hoy", "mejor_central", "compradores", "mis_ofertas", "ayuda", "borrar", "exportar", "pronostico", "vender_o_esperar"].includes(it) && !ex.kg && !ex.fecha && !ex.municipio && est.flujo.paso !== "precio";
    if (!cambia) return flujoOferta(D, est, texto, ex, ahora);
  }
  if (est.flujo && est.flujo.tipo === "respuesta") return registrarRespuestaTexto(D, est, texto, ex, ahora);
  if (ex.fruta) est.fruta = ex.fruta;
  let it = intencion(texto);
  // "Tengo 8 toneladas de limón…" es una oferta aunque contenga otras palabras (salvo que sea una pregunta de precio).
  if ((ex.kg || ex.cajas || ex.piezas) && ex.fruta && !["precio_hoy", "vender_o_esperar", "pronostico", "mejor_central"].includes(it)) it = "vender";
  if ((ex.kg || ex.cajas) && /\b(tengo|vendo|ofrezco|quiero vender|traigo)\b/.test(n)) it = "vender";
  if (!it && ex.municipio && n.split(" ").length <= 3) it = "perfil";
  if (!it && ex.fruta && n.split(" ").length <= 3) it = "precio_hoy";
  if (it === "vender" && /vendo o|o espero|o esperar/.test(n)) it = "vender_o_esperar";
  if (it === "perfil" || (/^soy de\b/.test(n))) return [perfil(D, est, texto, ex)];
  if (it === "saludo") return [saludo(D, est)];
  if (it === "ayuda") return [ayuda(D, est)];
  if (it === "gracias") return [{ texto: "Con gusto. Aquí estoy cuando lo necesite.", botones: menu(D, est) }];
  if (it === "borrar") return [{ texto: "¿Seguro que quiere borrar todo lo guardado en este teléfono (perfil, ofertas y conversaciones)? No se puede deshacer.",
    botones: [{ texto: "Sí, borrar todo", accion: { tipo: "borrar" } }, { texto: "No", enviar: "menu" }] }];
  if (it === "mis_ofertas") return [misOfertas(D, est)];
  if (it === "vender") {
    const b = { ...ex };
    if (!b.municipio && est.perfil && est.perfil.municipio) b.municipio = est.perfil.municipio;
    if (!b.fruta && est.perfil && est.perfil.cultivos && est.perfil.cultivos.length === 1) b.fruta = est.perfil.cultivos[0];
    delete b.precio;
    if (ex.precio !== undefined) b.precio = ex.precio;
    est.flujo = { tipo: "oferta", borrador: b, paso: null };
    est.flujo.paso = siguientePaso(b);
    const entendido = Object.keys(ex).filter((k) => ["fruta", "kg", "fecha", "municipio"].includes(k)).length;
    const msgs = [];
    if (entendido >= 2) msgs.push({ texto: `Entendí: ${resumenOferta(D, b)}.` });
    msgs.push(pedir(D, est, est.flujo.paso));
    return msgs;
  }
  if (/^(mas|más) compradores/.test(n)) {
    const o = (est.ofertas || []).find((x) => x.id === est.oferta_activa);
    if (o) return [{ texto: "Más compradores para su oferta:", tarjetas: { tipo: "compradores", oferta: o.id, lista: compradoresSugeridos(D, est, o, 20).slice(8) } }];
  }
  const fruta = ex.fruta || est.fruta || (est.perfil && est.perfil.cultivos && est.perfil.cultivos[0]);
  if (!it) {
    if (!fruta) return [{ texto: "No le entendí bien. Puede preguntarme por precios, centrales, compradores o decirme qué quiere vender.", botones: menu(D, est) }];
    it = "precio_hoy";
  }
  if (!fruta) { est.pendiente = it; return [preguntarFruta(D)]; }
  est.fruta = fruta;
  if (it === "precio_hoy") return [precioHoy(D, est, fruta)];
  if (it === "mejor_central") return [mejorCentral(D, est, fruta)];
  if (it === "demanda") return [demanda(D, est, fruta)];
  if (it === "compradores") {
    const o = { fruta, municipio: (est.perfil || {}).municipio, central: ex.central };
    return [{ texto: `Empresas que compran fruta y pueden interesarse en ${articulo(D, fruta)} (DENUE, INEGI; datos públicos, **sin verificar**):`, tarjetas: { tipo: "compradores", oferta: null, fruta, lista: compradoresSugeridos(D, est, o, 10) },
      botones: [{ texto: "Hacer una oferta", enviar: `quiero vender ${nombreFruta(D, fruta)}` }] }];
  }
  const r = respuestaObservatorio(D, fruta, it);
  if (r) return [{ ...r, botones: [{ texto: "Quiero vender", enviar: `quiero vender ${nombreFruta(D, fruta)}` }, { texto: "Precio de hoy", enviar: `precio ${nombreFruta(D, fruta)}` }] }];
  return [{ texto: "No le entendí bien.", botones: menu(D, est) }];
}

// ---------------------------------------------------------------- acciones de botones
export function accion(D, est, a, ahora = new Date()) {
  const idx = (est.ofertas || []).findIndex((o) => o.id === a.oferta);
  const o = idx >= 0 ? est.ofertas[idx] : null;
  const guardar = (x) => { est.ofertas[idx] = x; return x; };
  if (a.tipo === "contactar") {
    const c = ((D.compradores || {}).empresas || []).find((x) => x.id === a.comprador);
    if (!c) return { mensajes: [{ texto: "No encontré ese comprador." }] };
    const oferta = o || { fruta: a.fruta || est.fruta, municipio: (est.perfil || {}).municipio, fecha: null };
    const texto = mensajeOferta(D, est, oferta, c);
    const url = a.canal === "whatsapp" ? enlaceWhatsApp(c.tel, texto) : a.canal === "correo" ? enlaceCorreo(c.correo, `Oferta de ${nombreFruta(D, oferta.fruta).toLowerCase()} de Colima`, texto) : enlaceTelefono(c.tel);
    if (o) {
      let x = o.estado === "lista" ? cambiarEstado(o, "contactando", `contacto a ${c.nombre}`, ahora) : o;
      x = { ...x, contactos: [...x.contactos.filter((k) => k.comprador_id !== c.id), { comprador_id: c.id, nombre: c.nombre, tel: c.tel, canal: a.canal, fecha: ahora.toISOString(), respuesta: "sin_respuesta" }] };
      guardar(x);
    }
    return { abrir: url, mensajes: [{ texto: `Abrí ${a.canal === "whatsapp" ? "WhatsApp" : a.canal === "correo" ? "su correo" : "la llamada"} con ${c.nombre}${a.canal !== "telefono" ? " y el mensaje ya escrito. Revíselo y envíelo usted" : ""}. Cuando le respondan, anótelo aquí.`,
      botones: o ? [{ texto: "Anotar respuesta", accion: { tipo: "anotar", oferta: o.id, comprador: c.id } }] : [] }] };
  }
  if (a.tipo === "anotar") {
    est.flujo = { tipo: "respuesta", oferta: a.oferta, comprador: a.comprador };
    const c = (o.contactos || []).find((k) => k.comprador_id === a.comprador) || {};
    return { mensajes: [{ texto: `¿Qué le respondió ${c.nombre || "el comprador"}?`, botones: [{ texto: "Le interesa (ofreció precio)", enviar: "ofrece " }, { texto: "Pidió muestra o fotos", enviar: "pidió muestra" },
      { texto: "No le interesa", enviar: "no le interesa" }, { texto: "No contestó", enviar: "no contestó" }], escribir: "Ofrece $" }] };
  }
  if (a.tipo === "aceptar") {
    const c = (o.contactos || []).find((k) => k.comprador_id === a.comprador);
    let x = cambiarEstado(o, "acordada", `acuerdo con ${c.nombre} a $${f2(c.precio)}`, ahora);
    x = { ...x, trato: { comprador_id: c.comprador_id, comprador: c.nombre, tel: c.tel, precio: c.precio, kg: o.kg, piezas: o.piezas, fecha: o.fecha, entrega: o.entrega, municipio: o.municipio,
      total: c.precio * (o.kg || o.piezas || 0), anticipo_pct: 30, fecha_acuerdo: ahora.toISOString() } };
    guardar(x);
    return { mensajes: [{ texto: `¡Trato acordado con ${c.nombre}! ${f0(o.kg || o.piezas)} ${o.kg ? "kg" : "piezas"} a $${f2(c.precio)} = **$${f2(x.trato.total)}**. ` +
      "Le preparé el acuerdo de compraventa para que lo revisen, lo firmen y lo compartan. Recomendación: pida 30 % de anticipo a un comprador nuevo.",
      botones: [{ texto: "Ver acuerdo", accion: { tipo: "documento", documento: "acuerdo", oferta: o.id } }, { texto: "Enviar acuerdo por WhatsApp", accion: { tipo: "enviar_acuerdo", oferta: o.id } },
        { texto: "Registrar entrega", accion: { tipo: "entrega", oferta: o.id } }] }] };
  }
  if (a.tipo === "enviar_acuerdo") {
    const t = o.trato;
    const texto = `Confirmo nuestro acuerdo: ${resumenOferta(D, o)}. Precio $${f2(t.precio)} por ${o.kg ? "kg" : "pieza"}, total $${f2(t.total)}. Anticipo ${t.anticipo_pct} % y resto contra entrega. ¿De acuerdo?`;
    return { abrir: enlaceWhatsApp(t.tel, texto), mensajes: [{ texto: "Abrí WhatsApp con la confirmación del acuerdo ya escrita." }] };
  }
  if (a.tipo === "entrega") { est.flujo = { tipo: "respuesta", oferta: o.id, paso: "entrega" }; return { mensajes: [{ texto: "¿Cuántos kilos recibió el comprador (ya descontada la merma)?", escribir: "" }] }; }
  if (a.tipo === "cobro") { est.flujo = { tipo: "respuesta", oferta: o.id, paso: "cobro" }; return { mensajes: [{ texto: `¿Cuánto le pagaron en total? (El acuerdo decía $${f2(o.trato.total)}.)`, escribir: "" }] }; }
  if (a.tipo === "cancelar") { guardar(cambiarEstado(o, "cancelada", "cancelada por el productor", ahora)); return { mensajes: [{ texto: "Oferta cancelada." }] }; }
  if (a.tipo === "documento") return { documento: a.documento, oferta: o, mensajes: [] };
  if (a.tipo === "borrar") return { borrar: true, mensajes: [{ texto: "Borré todo lo guardado en este teléfono." }] };
  return { mensajes: [{ texto: "Acción no reconocida." }] };
}

function registrarRespuestaTexto(D, est, texto, ex, ahora) {
  const fl = est.flujo;
  const idx = est.ofertas.findIndex((o) => o.id === fl.oferta);
  let o = est.ofertas[idx];
  const n = normalizar(texto);
  const num = n.match(/(\d+(?:\.\d+)?)/);
  if (fl.paso === "entrega") {
    if (!num) return [{ texto: "Escriba los kilos recibidos, por ejemplo \"7800\"." }];
    const kg = Number(num[1]) * (/tonelada/.test(n) ? 1000 : 1);
    o = cambiarEstado(o, "entregada", `recibidos ${kg} kg`, ahora);
    o = { ...o, entrega: { kg_recibidos: kg, merma_kg: Math.max(0, (o.kg || 0) - kg), fecha: ahora.toISOString() } };
    o.trato = { ...o.trato, total_entregado: kg * o.trato.precio };
    est.ofertas[idx] = o; est.flujo = null;
    return [{ texto: `Entrega registrada: ${f0(kg)} kg (merma ${f0(o.entrega.merma_kg)} kg, ${o.kg ? f0(o.entrega.merma_kg / o.kg * 100) : 0} %). Le corresponden **$${f2(o.trato.total_entregado)}**.`,
      botones: [{ texto: "Registrar cobro", accion: { tipo: "cobro", oferta: o.id } }] }];
  }
  if (fl.paso === "cobro") {
    if (!num) return [{ texto: "Escriba el monto cobrado, por ejemplo \"150000\"." }];
    const monto = Number(num[1]);
    o = cambiarEstado(o, "cobrada", `cobrado $${monto}`, ahora);
    const esperado = o.trato.total_entregado || o.trato.total;
    o = { ...o, cobro: { monto, fecha: ahora.toISOString(), diferencia: monto - esperado } };
    o = cambiarEstado(o, "cerrada", "venta completa", ahora);
    est.ofertas[idx] = o; est.flujo = null;
    const kg = (o.entrega && o.entrega.kg_recibidos) || o.kg;
    return [{ texto: `**Venta cerrada.** Cobró $${f2(monto)}${monto < esperado ? ` ($${f2(esperado - monto)} menos de lo acordado)` : ""}. Precio logrado: $${f2(monto / kg)} por kg.`,
      botones: [{ texto: "Mis ofertas", enviar: "mis ofertas" }, { texto: "Nueva oferta", enviar: "quiero vender" }] }];
  }
  const c = o.contactos.find((k) => k.comprador_id === fl.comprador);
  if (!c) { est.flujo = null; return [{ texto: "No encontré a ese comprador en la oferta." }]; }
  if (/no le interesa|no interesa|no quiere|no compra/.test(n)) c.respuesta = "no_interesa";
  else if (/no contesto|no respondio|nada/.test(n)) c.respuesta = "sin_respuesta";
  else if (/muestra|foto/.test(n) && !num) c.respuesta = "muestra";
  else if (num) { c.respuesta = "contraoferta"; c.precio = Number(num[1]); }
  else return [{ texto: "No le entendí. ¿Ofreció un precio? Escriba la cifra, o toque una opción.", botones: [{ texto: "No le interesa", enviar: "no le interesa" }, { texto: "No contestó", enviar: "no contestó" }] }];
  c.fecha_respuesta = ahora.toISOString();
  if (c.respuesta === "contraoferta" && ["lista", "contactando", "negociando"].includes(o.estado)) {
    if (o.estado === "lista") o = cambiarEstado(o, "contactando", "contacto", ahora);
    o = cambiarEstado(o, "negociando", `${c.nombre} ofrece $${c.precio}`, ahora);
  }
  est.ofertas[idx] = o; est.flujo = null;
  if (c.respuesta === "contraoferta") {
    const ev = evaluarPropuesta(D, est, o, c.precio);
    return [{ texto: ev.texto, botones: [{ texto: `Aceptar $${f2(c.precio)}`, accion: { tipo: "aceptar", oferta: o.id, comprador: c.comprador_id } },
      { texto: "Contraofertar", accion: { tipo: "contactar", oferta: o.id, comprador: c.comprador_id, canal: "whatsapp" } }, { texto: "Buscar otro comprador", enviar: "mas compradores" }] }];
  }
  return [{ texto: { no_interesa: `Anotado: a ${c.nombre} no le interesa. Lo bajo en la lista.`, sin_respuesta: `Anotado: ${c.nombre} no contestó. Puede intentar de nuevo mañana o probar con otro.`,
    muestra: `Anotado: ${c.nombre} pidió muestra o fotos. Mándeselas por WhatsApp y vuelva a anotar su respuesta.` }[c.respuesta],
  botones: [{ texto: "Más compradores", enviar: "mas compradores" }, { texto: "Mis ofertas", enviar: "mis ofertas" }] }];
}

// ---------------------------------------------------------------- documentos (HTML para imprimir o guardar como PDF)
const esc = (s) => String(s == null ? "" : s).replace(/[&<>"]/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c]));

export function documentoFicha(D, est, o) {
  const s = sugerirPrecio(D, est, o);
  const p = est.perfil || {};
  return `<h1>Oferta de ${esc(nombreFruta(D, o.fruta).toLowerCase())} de Colima</h1><p class="m">Folio ${esc(o.id)} · ${esc(new Date(o.creada).toLocaleDateString("es-MX"))}</p>` +
    `<table><tr><th>Producto</th><td>${esc(nombreFruta(D, o.fruta))}${o.calibre ? ` #${esc(o.calibre)}` : ""}${o.variedad ? ` ${esc(o.variedad)}` : ""}${o.calidad ? `, ${esc(o.calidad)}` : ""}</td></tr>` +
    `<tr><th>Cantidad</th><td>${o.kg ? `${f0(o.kg)} kg` : `${f0(o.piezas)} piezas`}</td></tr><tr><th>Disponible</th><td>${esc(fechaLarga(o.fecha))}</td></tr>` +
    `<tr><th>Origen</th><td>${esc(o.municipio || p.municipio || "")}, Colima</td></tr><tr><th>Entrega</th><td>${o.entrega === "destino" ? "Puesto en destino" : "En huerta (el comprador recoge)"}</td></tr>` +
    `<tr><th>Empaque</th><td>${esc(o.empaque || "por acordar")}</td></tr><tr><th>Precio</th><td>${o.precio ? `$${f2(o.precio)} por ${o.piezas ? "pieza" : "kg"}` : "A propuesta del comprador"}</td></tr>` +
    `<tr><th>Productor</th><td>${esc(p.nombre || "—")}</td></tr></table>` +
    (s ? `<h2>Referencia de mercado</h2><p>${esc(corto(s.central))}, ${esc(fechaLarga(s.fecha))}: ${f2(s.precio_central)} ${esc(s.unidad)} de mayoreo (SNIIM).` +
      `${s.pronostico ? ` Pronóstico ${esc(s.pronostico.mes)}: ${f2(s.pronostico.precio)} (rango ${f2(s.pronostico.min)}–${f2(s.pronostico.max)}).` : ""}</p>` : "") +
    `<p class="m">Referencias calculadas por el Observatorio de Agro-Inteligencia Colimense con datos oficiales (SNIIM, SIAP). No es una garantía de precio.</p>`;
}

export function documentoAcuerdo(D, est, o) {
  const t = o.trato || {};
  const p = est.perfil || {};
  return `<h1>Acuerdo de compraventa de fruta</h1><p class="m">Folio ${esc(o.id)} · ${esc(new Date(t.fecha_acuerdo || Date.now()).toLocaleDateString("es-MX"))}</p>` +
    `<table><tr><th>Vendedor (productor)</th><td>${esc(p.nombre || "________________")}, ${esc(o.municipio || p.municipio || "")}, Colima</td></tr>` +
    `<tr><th>Comprador</th><td>${esc(t.comprador || "________________")}</td></tr><tr><th>Producto</th><td>${esc(resumenOferta(D, o))}</td></tr>` +
    `<tr><th>Precio</th><td>$${f2(t.precio)} por ${o.kg ? "kg" : "pieza"}</td></tr><tr><th>Cantidad acordada</th><td>${o.kg ? `${f0(o.kg)} kg` : `${f0(o.piezas)} piezas`}</td></tr>` +
    `<tr><th>Importe estimado</th><td>$${f2(t.total)} MXN</td></tr><tr><th>Entrega</th><td>${esc(fechaLarga(o.fecha))}, ${o.entrega === "destino" ? "en las instalaciones del comprador" : "en la huerta del vendedor"}</td></tr>` +
    `<tr><th>Pago</th><td>Anticipo de ${t.anticipo_pct || 30} % al confirmar y el resto contra entrega, sobre el peso recibido</td></tr>` +
    `<tr><th>Calidad</th><td>${esc(o.calidad || "primera")}; el comprador revisa al recibir y anota merma y motivo</td></tr></table>` +
    `<p>Las partes acuerdan lo anterior de buena fe. Cualquier diferencia de peso o calidad se registra por escrito al momento de la entrega.</p>` +
    `<div class="f"><div>Vendedor<br><br>__________________</div><div>Comprador<br><br>__________________</div></div>` +
    `<p class="m">Formato generado por el asistente del Observatorio de Agro-Inteligencia Colimense. El observatorio no es parte del acuerdo ni maneja el pago.</p>`;
}
