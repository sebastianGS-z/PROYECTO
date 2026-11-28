// Pruebas del motor del asistente (node --test tests/js). Usan los datos reales publicados en data/publico/asistente.
import test from "node:test";
import assert from "node:assert/strict";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const raiz = path.resolve(path.dirname(fileURLToPath(import.meta.url)), "../..");
const M = await import(path.join(raiz, "tablero/asistente/motor.js"));
const dir = path.join(raiz, "data/publico/asistente");
const leer = (f) => JSON.parse(fs.readFileSync(path.join(dir, f), "utf8"));
const base = leer("base.json");
const D = { base, frutas: Object.fromEntries(base.frutas.map((f) => [f.clave, leer(`fruta_${f.clave}.json`)])), compradores: leer("compradores.json") };
const HOY = new Date(2026, 10, 27); // viernes 27 de noviembre de 2026

// ------------------------------------------------------------ 150 frases de productor: intención esperada
const FRASES = [
  ["a cuanto esta el limon", "precio_hoy"], ["¿A cuánto está el limón?", "precio_hoy"], ["a como esta la papaya", "precio_hoy"],
  ["cuanto pagan el platano", "precio_hoy"], ["precio del coco", "precio_hoy"], ["como anda el precio del mango", "precio_hoy"],
  ["cuanto se paga la guayaba hoy", "precio_hoy"], ["cotizacion del aguacate", "precio_hoy"], ["a cuanto la sandia", "precio_hoy"],
  ["precio de la guanabana", "precio_hoy"], ["presio del limon", "precio_hoy"], ["a cuanto esta el limón en guadalajara", "precio_hoy"],
  ["vendo o espero", "vender_o_esperar"], ["me conviene vender ahora o esperar", "vender_o_esperar"], ["vendo ya o me espero un mes", "vender_o_esperar"],
  ["conviene esperar con la papaya", "vender_o_esperar"], ["aguantar o vender el limon", "vender_o_esperar"], ["espero o vendo", "vender_o_esperar"],
  ["el proximo mes a cuanto va a estar", "pronostico"], ["va a subir el limon", "pronostico"], ["va a bajar la papaya", "pronostico"],
  ["pronostico del platano", "pronostico"], ["que va a pasar con el precio", "pronostico"], ["como va a estar el mes que entra", "pronostico"],
  ["a que central mando mi limon", "mejor_central"], ["donde me pagan mas la papaya", "mejor_central"], ["cual central conviene", "mejor_central"],
  ["a donde mando el platano", "mejor_central"], ["en que plaza pagan mejor", "mejor_central"], ["que central me conviene", "mejor_central"],
  ["donde vendo mi coco", "mejor_central"], ["mejor central para guayaba", "mejor_central"], ["precios en otras centrales", "precio_hoy"],
  ["quien compra coco", "compradores"], ["quien me compra el limon", "compradores"], ["compradores de papaya", "compradores"],
  ["necesito una empacadora", "compradores"], ["bodegas que compren platano", "compradores"], ["a quien le vendo mi tamarindo", "compradores"],
  ["telefonos de compradores", "compradores"], ["dame contactos de clientes", "compradores"], ["quien compra guanabana", "compradores"],
  ["comprador de aguacate en monterrey", "compradores"], ["con quien vendo la sandia", "compradores"],
  ["puedo exportar", "exportar"], ["quiero exportar aguacate", "exportar"], ["venderle a estados unidos", "exportar"],
  ["exportacion de limon", "exportar"], ["mandar mango al extranjero", "exportar"], ["vender a otros paises", "exportar"], ["exportar a europa", "exportar"],
  ["cual es el mejor mes", "temporada"], ["en que temporada se paga mejor", "temporada"], ["que meses conviene vender papaya", "temporada"],
  ["cuando se paga mejor el limon", "temporada"], ["en que mes vendo el mango", "temporada"],
  ["hay demanda de aguacate", "demanda"], ["cuanto compran de limon", "demanda"], ["hay compradores para la guayaba", "demanda"], ["se vende bien el coco", "demanda"],
  ["cuanto deja una hectarea", "ingreso_ha"], ["cuanto deja una hectárea de limón", "ingreso_ha"], ["rendimiento por hectarea de papaya", "ingreso_ha"],
  ["me conviene sembrar otro cultivo", "cambiar_cultivo"], ["que sembrar en lugar de limon", "cambiar_cultivo"], ["cambiar de cultivo", "cambiar_cultivo"],
  ["que tanto puede bajar el precio", "riesgo"], ["que riesgo hay", "riesgo"], ["quien es la competencia", "competencia"], ["de donde llega mas limon", "competencia"],
  ["cuanto se produce en mi municipio", "produccion"], ["afecta la lluvia al precio", "clima"], ["el calor sube el precio", "clima"], ["y si viene un huracan", "clima"],
  ["esta caro o barato el limon", "caro_barato"], ["esta barato el platano", "caro_barato"], ["cuanto le llega al productor", "margen"],
  ["cuanto se queda el coyote", "margen"], ["cuanto me queda a mi", "margen"], ["como ha cambiado el precio en los ultimos años", "historia"],
  ["ha acertado el pronostico", "aciertos"], ["le atina el pronostico", "aciertos"], ["por que creerle a estos numeros", "confianza"], ["de donde salen los datos", "confianza"],
  ["es confiable", "confianza"],
  ["quiero vender", "vender"], ["quiero vender limon", "vender"], ["tengo papaya para vender", "vender"], ["ofrecer mi cosecha", "vender"],
  ["hacer una oferta", "vender"], ["tengo cosecha lista", "vender"], ["quiero colocar mi platano", "vender"], ["vendo coco", "vender"],
  ["mis ofertas", "mis_ofertas"], ["como van mis ventas", "mis_ofertas"], ["historial", "mis_ofertas"], ["seguimiento de mi oferta", "mis_ofertas"],
  ["soy de armeria", "perfil"], ["me llamo Juan", "perfil"], ["siembro limon y papaya", "perfil"],
  ["ayuda", "ayuda"], ["que puedes hacer", "ayuda"], ["menu", "ayuda"], ["como funciona", "ayuda"],
  ["hola", "saludo"], ["buenas tardes", "saludo"], ["buenos dias", "saludo"], ["que tal", "saludo"],
  ["gracias", "gracias"], ["muy amable", "gracias"], ["borrar mis datos", "borrar"], ["borra mis datos por favor", "borrar"],
  ["k onda cuanto pagan el limon", "precio_hoy"], ["cuanto esta pagando la central", "precio_hoy"], ["precio de hoy del tamarindo", "precio_hoy"],
  ["como esta el precio de la papaya maradol", "precio_hoy"], ["a como estan pagando el platano macho", "precio_hoy"],
  ["subira el precio del limon el mes que entra", "pronostico"], ["donde pagan mas el aguacate", "mejor_central"],
  ["quien compra limon en tecoman", "compradores"], ["necesito clientes para mi papaya", "compradores"], ["exportar papaya a canada", "exportar"],
  ["cuando conviene vender la sandia", "temporada"], ["cuanto me queda despues del intermediario", "margen"], ["quiero vender mi papaya", "vender"],
  ["buen dia", "saludo"], ["instrucciones", "ayuda"], ["como va mi oferta", "mis_ofertas"], ["opciones", "ayuda"],
];
// Ofertas completas: el motor debe reconocerlas como venta aunque traigan otras palabras.
const OFERTAS = [
  ["tengo 8 toneladas de limon #5 para el lunes en tecoman", { fruta: "limon", kg: 8000, calibre: "5", municipio: "Tecomán", fecha: "2026-11-30" }],
  ["tengo ocho toneladas de limón número 5 para el lunes", { fruta: "limon", kg: 8000, calibre: "5", fecha: "2026-11-30" }],
  ["vendo 500 kilos de papaya maradol mañana", { fruta: "papaya", kg: 500, variedad: "maradol", fecha: "2026-11-28" }],
  ["tengo 20 toneladas de platano macho en armeria", { fruta: "platano", kg: 20000, variedad: "macho", municipio: "Armería" }],
  ["traigo 3 mil piezas de coco para el viernes", { fruta: "coco", piezas: 3000, fecha: "2026-12-04" }],
  ["tengo 200 cajas de mango ataulfo de 20 kilos cada caja", { fruta: "mango", cajas: 200, kg_por_caja: 20, variedad: "ataulfo" }],
  ["tengo tonelada y media de tamarindo", { fruta: "tamarindo", kg: 1500 }],
  ["ofrezco 12 toneladas de limon a 15 pesos el kilo", { fruta: "limon", kg: 12000, precio: 15 }],
  ["tengo 2 toneladas de guayaba en coquimatlan para la proxima semana", { fruta: "guayaba", kg: 2000, municipio: "Coquimatlán", fecha: "2026-12-04" }],
  ["tengo 5 toneladas de aguacate hass", { fruta: "aguacate", kg: 5000, variedad: "hass" }],
  ["tengo 10 toneladas de sandia en ixtlahuacan para el 5 de diciembre", { fruta: "sandia", kg: 10000, municipio: "Ixtlahuacán", fecha: "2026-12-05" }],
  ["vendo 300 kg de guanabana en 3 dias", { fruta: "guanabana", kg: 300, fecha: "2026-11-30" }],
  ["tengo 8 toneladas de limon de segunda puesto en guadalajara", { fruta: "limon", kg: 8000, calidad: "segunda", entrega: "destino" }],
  ["tengo 4 toneladas de papaya en huerta", { fruta: "papaya", kg: 4000, entrega: "huerta" }],
  ["tengo 6 tons de limon para hoy", { fruta: "limon", kg: 6000, fecha: "2026-11-27" }],
  ["tengo cincuenta toneladas de limon", { fruta: "limon", kg: 50000 }],
  ["tengo 1,500 kilos de limon", { fruta: "limon", kg: 1500 }],
  ["tengo 7.5 toneladas de platano dominico", { fruta: "platano", kg: 7500, variedad: "dominico" }],
  ["tengo 9 toneladas de lemon", { fruta: "limon", kg: 9000 }],
  ["tengo 3 toneladas de papalla", { fruta: "papaya", kg: 3000 }],
  ["tengo 2 toneladas de platano para pasado mañana", { fruta: "platano", kg: 2000, fecha: "2026-11-29" }],
  ["vendo 100 cajas de limon", { fruta: "limon", cajas: 100 }],
  ["tengo 25 toneladas de limon en tecoman para el 2/12", { fruta: "limon", kg: 25000, municipio: "Tecomán", fecha: "2026-12-02" }],
  ["tengo 1 tonelada de coco pelado", { fruta: "coco", kg: 1000 }],
  ["tengo 40 toneladas de limon y lo llevo a la central", { fruta: "limon", kg: 40000, entrega: "destino" }],
];

test("reconoce la intención de 120 frases de productor (≥ 95 %)", () => {
  const fallos = FRASES.filter(([f, esperado]) => {
    const it = M.intencion(f);
    const ex = M.extraer(f, base, HOY);
    const efectivo = (ex.kg || ex.cajas || ex.piezas) && ex.fruta && !["precio_hoy", "vender_o_esperar", "pronostico", "mejor_central"].includes(it) ? "vender" : it;
    return efectivo !== esperado;
  });
  assert.ok(FRASES.length >= 120, `hay ${FRASES.length} frases`);
  assert.ok(fallos.length / FRASES.length <= 0.05, `fallan ${fallos.length}: ${JSON.stringify(fallos)}`);
});

test("extrae fruta, cantidad, precio, municipio y fecha de 25 ofertas", () => {
  for (const [frase, esperado] of OFERTAS) {
    const ex = M.extraer(frase, base, HOY);
    for (const [k, v] of Object.entries(esperado)) assert.deepEqual(ex[k], v, `${frase} → ${k}: ${ex[k]} ≠ ${v}`);
    const r = M.responder(D, {}, frase, HOY);
    assert.ok(r.length && r[r.length - 1].texto, frase);
  }
});

test("los números escritos con letra se convierten a cifras", () => {
  assert.equal(M.numerosALetra("ocho toneladas"), "8 toneladas");
  assert.equal(M.numerosALetra("dos mil kilos"), "2000 kilos");
  assert.equal(M.numerosALetra("veinte toneladas y media"), "20.5 toneladas");
  assert.equal(M.numerosALetra("una tonelada"), "1 tonelada");
  assert.equal(M.numerosALetra("quiero una oferta"), "quiero una oferta");
});

test("fechas relativas y por día de la semana", () => {
  assert.equal(M.fecha("manana", HOY), "2026-11-28");
  assert.equal(M.fecha("el lunes", HOY), "2026-11-30");
  assert.equal(M.fecha("el viernes", HOY), "2026-12-04"); // hoy es viernes: el próximo
  assert.equal(M.fecha("el 3 de enero", HOY), "2027-01-03");
  assert.equal(M.fecha("sin fecha", HOY), null);
});

// ------------------------------------------------------------ garantía de cifras
const numerosDe = (obj) => {
  const s = new Set();
  const visita = (x) => { if (typeof x === "number") { s.add(Math.abs(x).toFixed(2)); s.add(String(Math.round(x))); } else if (x && typeof x === "object") Object.values(x).forEach(visita); else if (typeof x === "string") (x.match(/\d+(?:\.\d+)?/g) || []).forEach((n) => { s.add(Number(n).toFixed(2)); s.add(String(Math.round(Number(n)))); }); };
  visita(obj);
  return s;
};

test("toda cifra de precio que dice el asistente existe en los datos del observatorio", () => {
  const consultas = ["a cuanto esta el limon", "precio de la papaya", "a que central mando mi platano", "vendo o espero el limon", "pronostico del aguacate",
    "puedo exportar aguacate", "hay demanda de guayaba", "esta caro el limon", "cuanto le llega al productor de papaya", "precio del coco", "precio de la sandia"];
  for (const q of consultas) {
    const est = { perfil: { municipio: "Tecomán" } };
    const msgs = M.responder(D, est, q, HOY);
    const fruta = est.fruta;
    const permitidos = numerosDe([D.frutas[fruta], base.municipios.find((m) => m.nombre === "Tecomán").km]);
    for (const m of msgs) {
      const precios = (m.texto.match(/\d[\d,]*\.\d{2}/g) || []).map((x) => x.replace(/,/g, ""));
      for (const p of precios) assert.ok(permitidos.has(Number(p).toFixed(2)), `"${q}": ${p} no aparece en los datos`);
    }
  }
});

// ------------------------------------------------------------ venta completa
test("una venta recorre los 8 estados y no permite saltos", () => {
  const est = {};
  M.responder(D, est, "soy de Tecomán", HOY);
  M.responder(D, est, "tengo 8 toneladas de limon #5 para el lunes", HOY);
  M.responder(D, est, "en huerta", HOY);
  M.responder(D, est, "que propongan", HOY);
  const r = M.responder(D, est, "si", HOY);
  const o = est.ofertas[0];
  assert.equal(o.estado, "lista");
  const c = r[0].tarjetas.lista.find((x) => x.tel);
  assert.ok(c, "hay al menos un comprador con teléfono");
  assert.throws(() => M.cambiarEstado(o, "cobrada"), /No se puede/);
  const a = M.accion(D, est, { tipo: "contactar", oferta: o.id, comprador: c.id, canal: "whatsapp" }, HOY);
  assert.match(a.abrir, /^https:\/\/wa\.me\/52\d{10}\?text=/);
  assert.match(decodeURIComponent(a.abrir), /8 toneladas de limón #5/);
  M.accion(D, est, { tipo: "anotar", oferta: o.id, comprador: c.id }, HOY);
  const ev = M.responder(D, est, "ofrece 9 pesos el kilo", HOY);
  assert.match(ev[0].texto, /\$9\.00/);
  M.accion(D, est, { tipo: "aceptar", oferta: o.id, comprador: c.id }, HOY);
  assert.equal(est.ofertas[0].trato.total, 72000);
  M.accion(D, est, { tipo: "entrega", oferta: o.id }, HOY);
  M.responder(D, est, "7800", HOY);
  M.accion(D, est, { tipo: "cobro", oferta: o.id }, HOY);
  const fin = M.responder(D, est, "70200", HOY);
  assert.match(fin[0].texto, /Venta cerrada/);
  assert.deepEqual(est.ofertas[0].historial.map((h) => h.estado), ["borrador", "lista", "contactando", "negociando", "acordada", "entregada", "cobrada", "cerrada"]);
  assert.match(M.documentoAcuerdo(D, est, est.ofertas[0]), /Acuerdo de compraventa/);
});

test("cancelar a mitad del flujo no guarda nada y un comprador que no quiso baja en la lista", () => {
  const est = {};
  M.responder(D, est, "quiero vender limon", HOY);
  M.responder(D, est, "cancelar", HOY);
  assert.equal(est.ofertas.length, 0);
  assert.equal(est.flujo, null);
  const o = M.nuevaOferta({ fruta: "limon", kg: 1000, municipio: "Tecomán" }, HOY);
  const primero = M.compradoresSugeridos(D, est, o)[0];
  est.ofertas = [{ ...o, contactos: [{ comprador_id: primero.id, respuesta: "no_interesa" }] }];
  assert.notEqual(M.compradoresSugeridos(D, est, o)[0].id, primero.id);
});

test("los compradores sugeridos son empresas con contacto y fuente DENUE", () => {
  const lista = M.compradoresSugeridos(D, { perfil: { municipio: "Tecomán" } }, { fruta: "coco" }, 10);
  assert.equal(lista.length, 10);
  for (const c of lista) assert.ok(c.tel || c.correo, c.nombre);
  assert.match(D.compradores.fuente, /DENUE/);
});

test("el precio sugerido usa referencias reales y el rango en huerta es menor que el mayoreo", () => {
  const s = M.sugerirPrecio(D, { perfil: { municipio: "Tecomán" } }, { fruta: "limon", calibre: "5", entrega: "huerta" });
  assert.ok(s.precio_central > 0 && s.huerta[1] <= s.precio_central && s.huerta[0] < s.huerta[1]);
  assert.ok(D.frutas.limon.hoy.some((h) => h.precio === s.precio_central));
});
