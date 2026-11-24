"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { API_BASE_URL } from "@/lib/api";

interface FieldMeta {
  key: string;
  label: string;
  type: string;
  category: string;
  public?: boolean;
  options?: string[];
  help?: string;
  value: any;
}

interface SettingsSchema {
  categories: { id: string; label: string }[];
  fields: Record<string, FieldMeta>;
}

const inputCls =
  "w-full px-3 py-2 text-xs bg-slate-50 rounded-xl border border-slate-300 focus:outline-none focus:ring-2 focus:ring-[#42677D]/30";

function FieldInput({
  field,
  value,
  onChange,
}: {
  field: FieldMeta;
  value: any;
  onChange: (v: any) => void;
}) {
  const strVal = value === null || value === undefined ? "" : String(value);

  if (field.type === "boolean") {
    return (
      <label className="inline-flex items-center gap-2 cursor-pointer">
        <input
          type="checkbox"
          checked={strVal === "true"}
          onChange={(e) => onChange(e.target.checked ? "true" : "false")}
          className="w-4 h-4 accent-[#42677D]"
        />
        <span className="text-xs text-slate-600">{strVal === "true" ? "Ativado" : "Desativado"}</span>
      </label>
    );
  }
  if (field.type === "textarea") {
    return <textarea rows={3} value={strVal} onChange={(e) => onChange(e.target.value)} className={inputCls} />;
  }
  if (field.type === "select" && field.options) {
    return (
      <select value={strVal} onChange={(e) => onChange(e.target.value)} className={inputCls}>
        {field.options.map((o) => (
          <option key={o} value={o}>{o}</option>
        ))}
      </select>
    );
  }
  if (field.type === "color") {
    return (
      <div className="flex items-center gap-2">
        <input type="color" value={/^#[0-9a-fA-F]{6}$/.test(strVal) ? strVal : "#42677D"} onChange={(e) => onChange(e.target.value)} className="w-10 h-9 rounded-lg border border-slate-300 cursor-pointer bg-white" />
        <input type="text" value={strVal} onChange={(e) => onChange(e.target.value)} className={inputCls + " flex-1"} placeholder="#RRGGBB" />
      </div>
    );
  }
  return (
    <input
      type={field.type === "number" || field.type === "integer" ? "number" : "text"}
      value={strVal}
      onChange={(e) => onChange(e.target.value)}
      className={inputCls}
    />
  );
}

export default function SiteSettingsPanel({ token }: { token: string }) {
  const [schema, setSchema] = useState<SettingsSchema | null>(null);
  const [values, setValues] = useState<Record<string, any>>({});
  const [dirty, setDirty] = useState<Set<string>>(new Set());
  const [activeCat, setActiveCat] = useState<string>("");
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState<{ type: "ok" | "err"; text: string } | null>(null);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE_URL}/admin/site-settings`, {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (!res.ok) throw new Error("Falha ao carregar");
      const data: SettingsSchema = await res.json();
      setSchema(data);
      const vals: Record<string, any> = {};
      Object.entries(data.fields).forEach(([k, f]) => (vals[k] = f.value));
      setValues(vals);
      setDirty(new Set());
      if (!activeCat && data.categories.length) setActiveCat(data.categories[0].id);
    } catch (e: any) {
      setMessage({ type: "err", text: e.message || "Erro ao carregar configurações" });
    } finally {
      setLoading(false);
    }
  }, [token, activeCat]);

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [token]);

  const fields = useMemo(() => {
    if (!schema) return [];
    return Object.values(schema.fields).filter((f) => f.category === activeCat);
  }, [schema, activeCat]);

  const setVal = (key: string, v: any) => {
    setValues((prev) => ({ ...prev, [key]: v }));
    setDirty((prev) => new Set(prev).add(key));
  };

  const handleSave = async () => {
    setSaving(true);
    setMessage(null);
    try {
      const payload: Record<string, any> = {};
      dirty.forEach((k) => (payload[k] = values[k]));
      const res = await fetch(`${API_BASE_URL}/admin/site-settings`, {
        method: "PUT",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${token}` },
        body: JSON.stringify({ configuracoes: payload }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Erro ao salvar");
      if (data.errors?.length) {
        setMessage({ type: "err", text: `${data.errors.length} campo(s) com erro: ${data.errors[0].error}` });
      } else {
        setMessage({ type: "ok", text: "Configurações salvas! O site reflete as mudanças no próximo carregamento." });
        setDirty(new Set());
        load();
      }
    } catch (e: any) {
      setMessage({ type: "err", text: e.message || "Erro ao salvar" });
    } finally {
      setSaving(false);
    }
  };

  const handleReset = async () => {
    if (!activeCat || !confirm(`Restaurar a categoria "${schema?.categories.find(c => c.id === activeCat)?.label}" aos padrões?`)) return;
    try {
      const res = await fetch(`${API_BASE_URL}/admin/site-settings/reset/${activeCat}`, {
        method: "POST",
        headers: { Authorization: `Bearer ${token}` },
      });
      const data = await res.json();
      setMessage({ type: "ok", text: data.message || "Categoria restaurada" });
      load();
    } catch {
      setMessage({ type: "err", text: "Erro ao restaurar" });
    }
  };

  if (loading && !schema) {
    return <div className="text-center py-12 text-slate-400 text-sm">Carregando configurações…</div>;
  }
  if (!schema) return null;

  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-xl font-black text-[#42677D]">Personalização do Site</h2>
        <p className="text-xs text-slate-500">
          Configure textos, prêmio, popup, aparência e regras do site sem alterar código. Campos marcados com 🌐 são públicos.
        </p>
      </div>

      {message && (
        <div className={`p-3 rounded-xl text-xs font-semibold ${message.type === "ok" ? "bg-emerald-50 text-emerald-700 border border-emerald-200" : "bg-red-50 text-red-700 border border-red-200"}`}>
          {message.text}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-[220px_1fr] gap-4">
        {/* Categorias */}
        <div className="flex lg:flex-col gap-1.5 overflow-x-auto lg:overflow-visible pb-2">
          {schema.categories.map((c) => (
            <button
              key={c.id}
              onClick={() => { setActiveCat(c.id); setMessage(null); }}
              className={`px-3 py-2 rounded-xl text-xs font-bold whitespace-nowrap text-left transition-all cursor-pointer ${
                activeCat === c.id ? "bg-[#42677D] text-white" : "bg-slate-100 text-slate-700 hover:bg-slate-200"
              }`}
            >
              {c.label}
            </button>
          ))}
        </div>

        {/* Campos */}
        <div className="bg-white p-5 rounded-2xl border border-slate-200 shadow-2xs space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="font-bold text-sm text-[#42677D]">
              {schema.categories.find((c) => c.id === activeCat)?.label}
            </h3>
            <button
              onClick={handleReset}
              className="text-[11px] font-bold text-slate-500 hover:text-red-600 cursor-pointer"
            >
              Restaurar padrão
            </button>
          </div>

          {fields.map((f) => (
            <div key={f.key}>
              <label className="block text-xs font-bold text-[#42677D] mb-1">
                {f.label}
                {!f.public && <span className="ml-1 text-slate-400 font-normal" title="Não exposto publicamente">🔒</span>}
              </label>
              <FieldInput field={f} value={values[f.key]} onChange={(v) => setVal(f.key, v)} />
              {f.help && <p className="text-[10px] text-slate-400 mt-1">{f.help}</p>}
            </div>
          ))}

          <div className="pt-3 border-t border-slate-100 flex items-center gap-3">
            <button
              onClick={handleSave}
              disabled={saving || dirty.size === 0}
              className="px-6 py-2.5 rounded-xl bg-[#42677D] hover:bg-[#345264] disabled:opacity-50 text-white text-xs font-bold shadow-xs cursor-pointer"
            >
              {saving ? "Salvando…" : dirty.size ? `Salvar (${dirty.size} alteração${dirty.size > 1 ? "ões" : ""})` : "Salvar"}
            </button>
            {dirty.size > 0 && (
              <button onClick={() => { setValues(Object.fromEntries(Object.entries(schema.fields).map(([k, f]) => [k, f.value]))); setDirty(new Set()); }} className="text-xs font-bold text-slate-500 hover:text-slate-700 cursor-pointer">
                Descartar
              </button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
