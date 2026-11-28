// Memoria privada del productor: vive solo en este navegador (IndexedDB). Nada se envía al observatorio.
// Si el navegador no permite IndexedDB (modo privado estricto), funciona en memoria y lo avisa.
const DB = "oaic-vende", TIENDA = "kv";
let disponible = true;

function abrir() {
  return new Promise((ok, mal) => {
    try {
      const r = indexedDB.open(DB, 1);
      r.onupgradeneeded = () => r.result.createObjectStore(TIENDA);
      r.onsuccess = () => ok(r.result);
      r.onerror = () => mal(r.error);
    } catch (e) { mal(e); }
  });
}

const enMemoria = {};

export async function leer(clave, porDefecto) {
  try {
    const db = await abrir();
    return await new Promise((ok) => {
      const q = db.transaction(TIENDA).objectStore(TIENDA).get(clave);
      q.onsuccess = () => ok(q.result === undefined ? porDefecto : q.result);
      q.onerror = () => ok(porDefecto);
    });
  } catch {
    disponible = false;
    return clave in enMemoria ? enMemoria[clave] : porDefecto;
  }
}

export async function guardar(clave, valor) {
  enMemoria[clave] = valor;
  try {
    const db = await abrir();
    await new Promise((ok, mal) => {
      const t = db.transaction(TIENDA, "readwrite");
      t.objectStore(TIENDA).put(JSON.parse(JSON.stringify(valor)), clave);
      t.oncomplete = ok; t.onerror = () => mal(t.error);
    });
  } catch { disponible = false; }
}

export async function borrarTodo() {
  for (const k of Object.keys(enMemoria)) delete enMemoria[k];
  try { await new Promise((ok) => { const r = indexedDB.deleteDatabase(DB); r.onsuccess = r.onerror = r.onblocked = ok; }); } catch { /* sin IndexedDB */ }
}

export function persistente() { return disponible; }

export function exportar(estado, chat) {
  const blob = new Blob([JSON.stringify({ esquema: "oaic-vende/1", exportado: new Date().toISOString(), estado, chat }, null, 1)], { type: "application/json" });
  const a = document.createElement("a");
  a.href = URL.createObjectURL(blob);
  a.download = `oaic-vende-respaldo-${new Date().toISOString().slice(0, 10)}.json`;
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 2000);
}

export async function importar(archivo) {
  const d = JSON.parse(await archivo.text());
  if (d.esquema !== "oaic-vende/1" || typeof d.estado !== "object") throw new Error("El archivo no es un respaldo del asistente.");
  return { estado: d.estado, chat: Array.isArray(d.chat) ? d.chat : [] };
}
