/**
 * Closed bilingual companion questions. No interpolation of native text, IDs or money.
 * Owning authority: PFOS Contract 14 section 11. Phase 14.1 (DC1). DC04/DC05/DC09/DC12.
 * A plan is not a domain result. No saved acknowledgement or fabricated measurements.
 */
import { parseDailyPlan, type Pillar, type DailyCycle } from './dailyPolicy.ts';
export type Locale = 'en' | 'ar';
const QUESTIONS: Record<Pillar, Record<Locale, string>> = {
  HIMAYAH: { en: 'Check the privacy or permission boundary before proceeding.', ar: 'راجع حدود الخصوصية والصلاحيات قبل المتابعة.' },
  SUKOON: { en: 'What would make today manageable?', ar: 'ما الذي يجعل اليوم أخف وأسهل؟' },
  THABAT: { en: 'Which open commitment needs the next small step?', ar: 'أي التزام مفتوح يحتاج خطوة صغيرة الآن؟' },
  MAL_PFOS: {
    en: 'A fresh PFOS alert needs review. Open the authoritative finance view for figures.',
    ar: 'هناك تنبيه حديث من PFOS يحتاج مراجعة. افتح العرض المالي المعتمد للأرقام.'
  },
  SHURA: { en: 'Which tradeoff needs a short discussion?', ar: 'أي مفاضلة تحتاج نقاشا قصيرا؟' },
  QARAR: { en: 'Which unresolved decision needs clearer criteria?', ar: 'أي قرار معلق يحتاج معايير أوضح؟' },
  BADAN: { en: 'What is a realistic movement or recovery step?', ar: 'ما الخطوة الواقعية للحركة أو التعافي؟' },
  YAWMIYAT: {
    en: 'Would reflecting on today help? Durable journal capture is unavailable here.',
    ar: 'هل يفيدك التأمل في اليوم؟ الحفظ الدائم لليوميات غير متاح هنا.'
  },
  TAFRIGH: {
    en: 'Would you like to unload without immediate advice? This is discussion, not durable capture.',
    ar: 'هل تريد التفريغ دون نصائح فورية؟ هذه محادثة وليست حفظا دائما.'
  },
  NAQD: { en: 'Which assumption would benefit from a focused challenge?', ar: 'أي افتراض يستفيد من نقد مركز؟' },
};
const TITLES: Record<DailyCycle, Record<Locale, string>> = {
  morning: { en: 'Morning focus', ar: 'تركيز الصباح' },
  midday: { en: 'A small course correction', ar: 'تعديل بسيط للمسار' },
  evening: { en: 'Evening reflection', ar: 'تأمل المساء' },
  weekly: { en: 'Weekly review of available signals', ar: 'مراجعة أسبوعية للإشارات المتاحة' },
};

/**
 * READ access to the closed question set, added for NIZAM-SLACK-FINANCE-007 track_t.
 *
 * This is the whole of the pillar seam and it is deliberately one-way. A caller may READ a pillar's
 * question; it cannot extend, template or interpolate into it, because QUESTIONS stays private and no
 * setter exists. New capability therefore arrives as a separate typed structure alongside this string
 * rather than as a substitution inside it, which is what keeps the closed-set rule intact and the
 * pillar count at ten.
 */
export function pillarQuestion(pillar: Pillar, locale: Locale): string {
  if (locale !== 'en' && locale !== 'ar') throw new Error('DAILY_LOCALE_INVALID');
  return QUESTIONS[pillar][locale];
}

export function renderDailyMessage(raw: unknown, locale: Locale): string {
  if (locale !== 'en' && locale !== 'ar') throw new Error('DAILY_LOCALE_INVALID');
  const plan = parseDailyPlan(raw);
  const downshift = plan.capacity === 'low' || plan.capacity === 'unknown';
  const pacing = downshift ? (locale === 'en' ? 'Keep it small. No pressure to optimize.' : 'خطوة صغيرة تكفي. لا ضغط للتحسين.') : '';
  return [TITLES[plan.cycle][locale], pacing, ...plan.items.map(item => QUESTIONS[item.pillar][locale])]
    .filter(Boolean).join('\n');
}
