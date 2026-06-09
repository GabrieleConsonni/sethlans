// Configurazione dell'interfaccia.
//
// READONLY — modalità sola lettura. In una prima versione la board è
// modificabile SOLTANTO dagli Agenti AI (via HTTP), mai dall'utente dalla UI.
// Questo flag nasconde tutte le affordance di scrittura del frontend
// (creazione/modifica/eliminazione, drag-and-drop, editor dei documenti):
// la navigazione e la consultazione restano disponibili.
//
// L'API REST del backend resta comunque aperta: questo è un vincolo di
// prodotto sull'interfaccia, non una barriera di sicurezza. Default: true.
// Per riabilitare l'editing dalla UI: VITE_READONLY=false.
const raw = import.meta.env.VITE_READONLY;
export const READONLY =
  raw === undefined ? true : !(raw === "false" || raw === "0" || raw === false);
