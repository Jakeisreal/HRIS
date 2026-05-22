import React, { useEffect, useMemo, useState } from 'react'
import {
  Activity,
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  BarChart3,
  BriefcaseBusiness,
  CheckCircle2,
  ChevronRight,
  Copy,
  Database,
  Download,
  Eye,
  FileSpreadsheet,
  Filter,
  Globe2,
  Home,
  KeyRound,
  LayoutDashboard,
  Lock,
  LogIn,
  LogOut,
  Search,
  Settings2,
  Share2,
  ShieldAlert,
  ShieldCheck,
  Star,
  UploadCloud,
  User,
  Users,
} from 'lucide-react'

const candidates = [
  { id: 'E24017', name: '김도현', dept: '품질관리팀', position: '과장', tenure: 12.4, performance: 'A', leadership: 'A', language: 'TOEIC 890', languageScore: 890, overseas: '중국 주재 24개월', overseasMonths: 24, certificate: '품질경영기사', expatFit: 92, leaderFit: 87, purpose: ['주재원', '차기 팀장'], strengths: ['중국 주재 경험', '품질 안정화', '평가 우수'], cautions: ['조직관리 경험 추가 확인'] },
  { id: 'E21884', name: '박준호', dept: '영업팀', position: '차장', tenure: 15.1, performance: 'A', leadership: 'A', language: 'TOEIC 930', languageScore: 930, overseas: '인도 파견 18개월', overseasMonths: 18, certificate: '무역영어', expatFit: 95, leaderFit: 91, purpose: ['주재원', '차기 팀장'], strengths: ['어학 우수', '해외 고객 대응', '장기 근속'], cautions: ['제조/품질 실무 경험 확인'] },
  { id: 'E22615', name: '윤지훈', dept: '설계팀', position: '과장', tenure: 9.4, performance: 'B+', leadership: 'A', language: 'TOEIC 840', languageScore: 840, overseas: '미국 주재 30개월', overseasMonths: 30, certificate: '기계설계기사', expatFit: 86, leaderFit: 84, purpose: ['주재원', '차기 팀장'], strengths: ['미국 장기 주재', '설계 전문성', '실행력 우수'], cautions: ['최근 평가 추이 확인'] },
  { id: 'E20991', name: '정하늘', dept: '인사팀', position: '과장', tenure: 10.2, performance: 'A', leadership: 'A', language: 'OPIc IH', languageScore: 880, overseas: '중국 출장 6개월', overseasMonths: 6, certificate: 'HRM전문가', expatFit: 80, leaderFit: 88, purpose: ['차기 팀장'], strengths: ['커뮤니케이션', '평가 안정성', '조직 이해도'], cautions: ['장기 해외 경험 제한'] },
  { id: 'E25276', name: '최민재', dept: '구매팀', position: '대리', tenure: 5.6, performance: 'B', leadership: 'B', language: 'TOEIC 760', languageScore: 760, overseas: '없음', overseasMonths: 0, certificate: 'CPIM', expatFit: 69, leaderFit: 73, purpose: ['차기 팀장'], strengths: ['구매 프로세스 이해', '원가 감각'], cautions: ['해외 경험 부족', '리더십 추가 검증'] },
]

const templates = [
  { id: 'expat-basic', name: '주재원 기본 템플릿', purpose: '주재원', scope: '기본 제공', count: 86, owner: 'System', filters: ['TOEIC 800 이상', '최근 평가 A 이상', '해외 경험 보유', '근속 5년 이상'] },
  { id: 'leader-basic', name: '차기 팀장 기본 템플릿', purpose: '차기 팀장', scope: '기본 제공', count: 124, owner: 'System', filters: ['최근 3년 평균 B+ 이상', '리더십 A 이상', '근속 7년 이상', '조직관리 가능성'] },
  { id: 'china-expat', name: '중국 법인 주재원 후보', purpose: '주재원', scope: '인사팀 공유', count: 42, owner: '김지석', filters: ['중국 경험 우대', '품질/생산기술', 'TOEIC 750 이상', '최근 평가 B+ 이상'] },
  { id: 'quality-leader', name: '품질 부문 차기 리더 후보', purpose: '차기 팀장', scope: '나만 보기', count: 17, owner: '김지석', filters: ['품질 조직', '리더십 A 이상', '최근 평가 A 이상', '근속 8년 이상'] },
]

const uploads = [
  { file: 'HR_candidate_master_20260522.xlsx', at: '2026.05.22 09:34', user: '배승혜', rows: 1248, success: 1180, newRows: 45, changes: 210, dup: 12, errors: 5, status: '오류 확인 필요' },
  { file: 'HR_candidate_master_20260521.xlsx', at: '2026.05.21 09:12', user: '김지석', rows: 1236, success: 1236, newRows: 29, changes: 144, dup: 8, errors: 0, status: '정상 반영' },
]

const audits = [
  { time: '2026-05-22 09:12', user: '김지석', role: '인사담당자', action: '상세 조회', target: '김도현 / E24017', result: '성공', risk: '정상', ip: '10.21.4.15' },
  { time: '2026-05-22 09:20', user: '김지석', role: '인사담당자', action: '목록 다운로드', target: '주재원 후보 목록.xlsx', result: '성공', risk: '주의', ip: '10.21.4.15' },
  { time: '2026-05-22 09:34', user: '배승혜', role: '인사담당자', action: '엑셀 업로드', target: 'HR_candidate_master_20260522.xlsx', result: '성공', risk: '정상', ip: '10.21.4.21' },
  { time: '2026-05-22 10:02', user: '박민수', role: '팀장/조회자', action: '권한 차단', target: '/data/upload', result: '차단', risk: '위험', ip: '10.21.7.80' },
  { time: '2026-05-22 10:14', user: '김지석', role: '인사담당자', action: '템플릿 적용', target: '중국 법인 주재원 후보', result: '성공', risk: '정상', ip: '10.21.4.15' },
]

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '')

function isApiEnabled() {
  return API_BASE_URL.length > 0
}

async function apiFetch(path, options) {
  const response = await fetch(`${API_BASE_URL}${path}`, options)
  const payload = await response.json().catch(() => ({}))
  if (!response.ok) {
    throw new Error(payload.error || `API 요청 실패: ${response.status}`)
  }
  return payload
}

async function fetchCandidateRows() {
  const payload = await apiFetch('/api/candidates')
  return (payload.items || []).map(mapApiCandidate)
}

async function uploadCandidateFile(file, { dryRun }) {
  const formData = new FormData()
  formData.append('file', file)
  if (dryRun) formData.append('dry_run', 'true')
  return apiFetch('/api/candidates/upload', {
    method: 'POST',
    body: formData,
  })
}

function mapApiCandidate(row) {
  const purpose = parsePurpose(row.purpose)
  return {
    id: row.employee_id,
    name: row.name,
    dept: row.dept || '-',
    position: row.position || '-',
    tenure: Number(row.tenure || 0),
    performance: row.performance || '-',
    leadership: row.leadership || '-',
    language: row.language || '-',
    languageScore: Number(row.language_score || 0),
    overseas: row.overseas || '-',
    overseasMonths: Number(row.overseas_months || 0),
    certificate: row.certificate || '-',
    expatFit: Number(row.expat_fit || 0),
    leaderFit: Number(row.leader_fit || 0),
    purpose: purpose.length ? purpose : ['주재원'],
    strengths: ['업로드 데이터 반영'],
    cautions: [],
  }
}

function parsePurpose(value) {
  if (!value) return []
  if (Array.isArray(value)) return value
  try {
    const parsed = JSON.parse(value)
    if (Array.isArray(parsed)) return parsed
  } catch {
    // Plain Excel values are handled below.
  }
  return String(value).split(/[,\n/]+/).map((item) => item.trim()).filter(Boolean)
}

const nav = [
  { key: 'dashboard', label: '홈 대시보드', icon: LayoutDashboard, roles: ['hr', 'viewer'] },
  { key: 'candidates', label: '후보자 목록', icon: Users, roles: ['hr', 'viewer'] },
  { key: 'detail', label: '후보자 상세', icon: User, roles: ['hr', 'viewer'] },
  { key: 'compare', label: '후보자 비교', icon: BarChart3, roles: ['hr', 'viewer'] },
  { key: 'templates', label: '템플릿 관리', icon: Filter, roles: ['hr'] },
  { key: 'upload', label: '데이터 관리', icon: Database, roles: ['hr'] },
  { key: 'audit', label: '감사 로그', icon: ShieldCheck, roles: ['hr'] },
]

function Badge({ children, tone = 'default' }) {
  const map = {
    default: 'bg-slate-100 text-slate-700 ring-slate-200',
    blue: 'bg-blue-50 text-blue-700 ring-blue-100',
    green: 'bg-emerald-50 text-emerald-700 ring-emerald-100',
    amber: 'bg-amber-50 text-amber-700 ring-amber-100',
    red: 'bg-rose-50 text-rose-700 ring-rose-100',
    purple: 'bg-violet-50 text-violet-700 ring-violet-100',
    dark: 'bg-slate-900 text-white ring-slate-800',
  }
  return <span className={`inline-flex items-center rounded-full px-2.5 py-1 text-xs font-bold ring-1 ${map[tone]}`}>{children}</span>
}

function Card({ children, className = '' }) {
  return <section className={`rounded-3xl border border-slate-200 bg-white shadow-sm ${className}`}>{children}</section>
}

function CardHeader({ icon: Icon, title, subtitle, right }) {
  return (
    <div className="flex items-start justify-between gap-4 border-b border-slate-100 px-5 py-4">
      <div className="flex items-start gap-3">
        {Icon && <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl bg-slate-100 text-slate-700"><Icon className="h-5 w-5" /></div>}
        <div>
          <h3 className="text-sm font-black text-slate-900">{title}</h3>
          {subtitle && <p className="mt-1 text-xs text-slate-500">{subtitle}</p>}
        </div>
      </div>
      {right}
    </div>
  )
}

function Metric({ label, value, sub, icon: Icon, tone = 'default' }) {
  const map = {
    default: 'bg-slate-100 text-slate-700',
    blue: 'bg-blue-50 text-blue-700',
    green: 'bg-emerald-50 text-emerald-700',
    amber: 'bg-amber-50 text-amber-700',
    red: 'bg-rose-50 text-rose-700',
    purple: 'bg-violet-50 text-violet-700',
  }
  return (
    <div className="rounded-3xl border border-slate-200 bg-white p-5 shadow-sm">
      <div className="flex items-start justify-between gap-4">
        <div>
          <p className="text-xs font-bold text-slate-500">{label}</p>
          <p className="mt-2 text-3xl font-black tracking-tight text-slate-900">{value}</p>
          {sub && <p className="mt-1 text-xs font-semibold text-slate-500">{sub}</p>}
        </div>
        <div className={`flex h-11 w-11 items-center justify-center rounded-2xl ${map[tone]}`}><Icon className="h-5 w-5" /></div>
      </div>
    </div>
  )
}

function LoginPage({ setAuthed, setPage, role, setRole }) {
  return (
    <div className="grid min-h-screen grid-cols-1 bg-slate-100 xl:grid-cols-[1.1fr_0.9fr]">
      <section className="hidden bg-slate-950 p-12 text-white xl:flex xl:flex-col xl:justify-between">
        <div className="flex items-center gap-3"><div className="flex h-12 w-12 items-center justify-center rounded-2xl bg-white text-sm font-black text-slate-950">HS</div><div><p className="text-lg font-black">HR Talent Support</p><p className="text-sm font-semibold text-white/60">웹 기반 인사 업무 지원 시스템</p></div></div>
        <div className="max-w-2xl"><Badge tone="blue">Role-Based Access</Badge><h1 className="mt-5 text-5xl font-black leading-tight tracking-tight">후보자 선별부터<br />감사 로그까지 한 흐름으로.</h1><p className="mt-5 text-lg font-semibold leading-8 text-white/65">주재원 및 차기 팀장 후보 선별을 검색, 필터, 상세 분석, 비교, 데이터 업로드, 감사 추적으로 연결합니다.</p></div>
        <div className="grid grid-cols-3 gap-3"><HeroMetric icon={Search} label="검색/필터" value="실시간" /><HeroMetric icon={BarChart3} label="분석/비교" value="대시보드" /><HeroMetric icon={ShieldCheck} label="보안/로그" value="추적" /></div>
      </section>
      <section className="flex items-center justify-center p-6">
        <Card className="w-full max-w-md overflow-hidden">
          <div className="border-b border-slate-100 p-6"><div className="mb-5 flex h-14 w-14 items-center justify-center rounded-3xl bg-slate-900 text-white"><ShieldCheck className="h-7 w-7" /></div><h2 className="text-2xl font-black tracking-tight">로그인</h2><p className="mt-2 text-sm font-semibold leading-6 text-slate-500">인증 후 역할에 따라 메뉴 접근 범위를 제어합니다.</p></div>
          <div className="space-y-4 p-6">
            <Input label="아이디 / 사번" icon={User} defaultValue="E24017" />
            <Input label="비밀번호" icon={KeyRound} defaultValue="password" type="password" />
            <div><label className="mb-1.5 block text-xs font-black text-slate-600">시연 권한</label><div className="grid grid-cols-2 gap-2"><button onClick={() => setRole('hr')} className={`rounded-2xl border px-3 py-3 text-sm font-black ${role === 'hr' ? 'border-slate-900 bg-slate-900 text-white' : 'border-slate-200 bg-white text-slate-700'}`}>인사담당자</button><button onClick={() => setRole('viewer')} className={`rounded-2xl border px-3 py-3 text-sm font-black ${role === 'viewer' ? 'border-slate-900 bg-slate-900 text-white' : 'border-slate-200 bg-white text-slate-700'}`}>팀장/조회자</button></div></div>
            <button onClick={() => { setAuthed(true); setPage('dashboard') }} className="inline-flex h-12 w-full items-center justify-center gap-2 rounded-2xl bg-slate-900 px-4 text-sm font-black text-white shadow-sm hover:bg-slate-800"><LogIn className="h-4 w-4" /> 로그인</button>
          </div>
        </Card>
      </section>
    </div>
  )
}

function Input({ label, icon: Icon, defaultValue, type = 'text' }) {
  return <div><label className="mb-1.5 block text-xs font-black text-slate-600">{label}</label><div className="relative"><Icon className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" /><input type={type} defaultValue={defaultValue} className="h-11 w-full rounded-2xl border border-slate-200 bg-slate-50 pl-10 pr-4 text-sm font-bold outline-none focus:border-slate-900 focus:bg-white" /></div></div>
}

function HeroMetric({ icon: Icon, label, value }) {
  return <div className="rounded-3xl bg-white/10 p-5 ring-1 ring-white/10"><Icon className="h-6 w-6 text-white/70" /><p className="mt-4 text-xs font-bold text-white/50">{label}</p><p className="mt-1 text-xl font-black text-white">{value}</p></div>
}

function AppShell({ role, setRole, page, setPage, children }) {
  const current = nav.find((item) => item.key === page)
  const isAllowed = current?.roles.includes(role)
  return (
    <div className="min-h-screen bg-slate-100 text-slate-900">
      <div className="flex min-h-screen">
        <aside className="hidden w-64 shrink-0 border-r border-slate-200 bg-white lg:block">
          <div className="border-b border-slate-200 px-6 py-5"><div className="flex items-center gap-3"><div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-slate-900 text-sm font-black text-white">HS</div><div><p className="text-sm font-black tracking-tight">HR Talent Support</p><p className="text-xs text-slate-500">화신 인사 업무 지원</p></div></div></div>
          <nav className="space-y-1 px-3 py-4 text-sm">
            {nav.map((item) => {
              const Icon = item.icon
              const allowed = item.roles.includes(role)
              const active = page === item.key
              return <button key={item.key} onClick={() => allowed ? setPage(item.key) : setPage('forbidden')} className={`flex w-full items-center justify-between rounded-xl px-3 py-2.5 text-left font-semibold transition ${active ? 'bg-slate-900 text-white shadow-sm' : allowed ? 'text-slate-600 hover:bg-slate-50' : 'text-slate-300'}`}><span className="flex items-center gap-3"><Icon className="h-4 w-4" />{item.label}</span>{!allowed && <Lock className="h-3.5 w-3.5" />}</button>
            })}
          </nav>
        </aside>
        <main className="min-w-0 flex-1">
          <header className="sticky top-0 z-20 border-b border-slate-200 bg-white/90 backdrop-blur">
            <div className="flex flex-col gap-4 px-6 py-4 xl:flex-row xl:items-center xl:justify-between"><div><div className="text-xs font-semibold text-slate-500">{current?.label || '접근 차단'}</div><div className="mt-1 flex flex-wrap items-center gap-2"><h1 className="text-2xl font-black tracking-tight">{current?.label || '접근 권한 없음'}</h1><Badge tone={role === 'hr' ? 'blue' : 'amber'}>{role === 'hr' ? '인사담당자' : '팀장/조회자'}</Badge><Badge tone="dark">기준일 2026.05.22</Badge></div></div><div className="flex flex-wrap items-center gap-2"><select value={role} onChange={(e) => setRole(e.target.value)} className="h-10 rounded-xl border border-slate-200 bg-white px-3 text-sm font-black text-slate-700 shadow-sm outline-none focus:border-slate-900"><option value="hr">인사담당자</option><option value="viewer">팀장/조회자</option></select><button onClick={() => setPage('login')} className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-black text-slate-700 shadow-sm hover:bg-slate-50"><LogOut className="h-4 w-4" /> 로그아웃</button></div></div>
          </header>
          {!isAllowed && page !== 'forbidden' ? <ForbiddenPage setPage={setPage} role={role} /> : children}
        </main>
      </div>
    </div>
  )
}

function DashboardPage({ setPage, role, candidateRows, setSelectedCandidate }) {
  const canManage = role === 'hr'
  return (
    <div className="space-y-5 p-5">
      <Card className="overflow-hidden"><div className="grid grid-cols-1 xl:grid-cols-[minmax(0,1fr)_360px]"><div className="p-6"><div className="flex flex-wrap items-center gap-2"><Badge tone="green">데이터 정상 연동</Badge><Badge tone="amber">오류 5건 확인 필요</Badge></div><h2 className="mt-5 text-4xl font-black leading-tight tracking-tight text-slate-900">데이터 기반 후보자 선별을 한 화면에서 시작합니다.</h2><p className="mt-4 max-w-3xl text-base font-semibold leading-7 text-slate-500">목적별 템플릿을 적용해 후보군을 압축하고, 상세 대시보드와 비교 화면에서 평가·어학·리더십·해외 경험을 검토합니다.</p><div className="mt-6 flex flex-wrap gap-2"><button onClick={() => setPage('candidates')} className="inline-flex items-center gap-2 rounded-2xl bg-slate-900 px-5 py-3 text-sm font-black text-white shadow-sm"><Globe2 className="h-4 w-4" /> 주재원 후보 선별</button><button onClick={() => setPage('candidates')} className="inline-flex items-center gap-2 rounded-2xl border border-slate-200 bg-white px-5 py-3 text-sm font-black text-slate-700 shadow-sm hover:bg-slate-50"><BriefcaseBusiness className="h-4 w-4" /> 차기 팀장 후보 선별</button></div></div><div className="border-t border-slate-100 bg-slate-50 p-6 xl:border-l xl:border-t-0"><div className="rounded-3xl bg-white p-5 ring-1 ring-slate-200"><p className="text-xs font-bold text-slate-500">최근 데이터 기준일</p><p className="mt-1 text-2xl font-black text-slate-900">2026.05.22</p><div className="mt-5 space-y-3"><StatusRow label="검증 성공" value="1,180건" /><StatusRow label="오류" value="5건" danger /><StatusRow label="최근 업로드" value="09:34" /></div></div></div></div></Card>
      <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4"><Metric label="전체 후보자" value="1,248" sub="최근 업로드 기준" icon={Users} /><Metric label="주재원 후보" value="86" sub="기본 템플릿 기준" icon={Globe2} tone="blue" /><Metric label="차기 팀장 후보" value="124" sub="기본 템플릿 기준" icon={BriefcaseBusiness} tone="amber" /><Metric label="데이터 오류" value="5" sub="검증 결과 확인 필요" icon={AlertTriangle} tone="red" /></div>
      <div className="grid grid-cols-1 gap-5 xl:grid-cols-[minmax(0,1fr)_390px]"><Card><CardHeader icon={LayoutDashboard} title="빠른 실행" subtitle="주요 업무 화면으로 즉시 이동합니다." /><div className="grid grid-cols-1 gap-4 p-5 md:grid-cols-2"><QuickAction title="후보자 목록" desc="검색·필터·정렬로 후보군 압축" icon={Search} onClick={() => setPage('candidates')} primary /><QuickAction title="후보자 비교" desc="선택 후보 2~3명 비교" icon={BarChart3} onClick={() => setPage('compare')} primary />{canManage && <QuickAction title="엑셀 업로드" desc="원천 데이터 갱신" icon={UploadCloud} onClick={() => setPage('upload')} />}{canManage && <QuickAction title="감사 로그" desc="조회·다운로드 이력 추적" icon={ShieldCheck} onClick={() => setPage('audit')} />}</div></Card><NoticePanel /></div>
      <div className="grid grid-cols-1 gap-5 xl:grid-cols-2"><RecommendedPanel setPage={setPage} rows={candidateRows} setSelectedCandidate={setSelectedCandidate} /><RecentTemplatePanel setPage={setPage} canManage={canManage} /></div>
      <UploadStatusPanel setPage={setPage} canManage={canManage} />
    </div>
  )
}

function StatusRow({ label, value, danger }) { return <div className="flex items-center justify-between gap-3 rounded-2xl bg-slate-50 p-3 ring-1 ring-slate-200"><p className="text-xs font-black text-slate-500">{label}</p><p className={`text-right text-xs font-black ${danger ? 'text-rose-700' : 'text-slate-800'}`}>{value}</p></div> }
function QuickAction({ title, desc, icon: Icon, onClick, primary = false }) { return <button onClick={onClick} className={`group min-h-32 rounded-3xl border p-5 text-left transition ${primary ? 'border-slate-900 bg-slate-900 text-white shadow-lg' : 'border-slate-200 bg-white text-slate-900 hover:shadow-md'}`}><div className="flex items-start justify-between"><div className={`flex h-12 w-12 items-center justify-center rounded-2xl ${primary ? 'bg-white/10' : 'bg-slate-100'}`}><Icon className="h-6 w-6" /></div><ArrowRight className={`h-5 w-5 transition group-hover:translate-x-1 ${primary ? 'text-white/70' : 'text-slate-400'}`} /></div><h3 className="mt-5 text-lg font-black tracking-tight">{title}</h3><p className={`mt-2 text-sm font-semibold leading-6 ${primary ? 'text-white/65' : 'text-slate-500'}`}>{desc}</p></button> }
function NoticePanel() { return <Card><CardHeader icon={AlertTriangle} title="확인 필요 알림" subtitle="업무 전 확인 이벤트" right={<Badge tone="amber">3건</Badge>} /><div className="space-y-3 p-5"><Notice tone="amber" icon={FileSpreadsheet} title="최근 업로드 데이터 오류 5건" desc="고과등급, 입사일자, 사번, TOEIC 점수, 조직명 오류 확인 필요" /><Notice tone="red" icon={ShieldAlert} title="권한 차단 이벤트 1건" desc="팀장/조회자의 데이터 업로드 직접 URL 접근이 차단됨" /><Notice tone="blue" icon={Share2} title="공유 템플릿 활성화" desc="중국 법인 주재원 후보 템플릿이 인사팀에 공유 중" /></div></Card> }
function Notice({ tone, icon: Icon, title, desc }) { const cls = tone === 'red' ? 'bg-rose-50 text-rose-800 ring-rose-100' : tone === 'blue' ? 'bg-blue-50 text-blue-800 ring-blue-100' : 'bg-amber-50 text-amber-800 ring-amber-100'; return <div className={`rounded-2xl p-4 ring-1 ${cls}`}><div className="flex items-start gap-3"><Icon className="mt-0.5 h-5 w-5 shrink-0" /><div><p className="text-sm font-black">{title}</p><p className="mt-1 text-sm font-semibold leading-6 opacity-90">{desc}</p></div></div></div> }
function RecommendedPanel({ setPage, rows = candidates, setSelectedCandidate }) { const sorted = [...rows].sort((a, b) => b.expatFit - a.expatFit).slice(0, 4); return <Card><CardHeader icon={Star} title="추천 후보 Top 4" subtitle="기본 템플릿 기준 상위 후보" /><div className="space-y-3 p-5">{sorted.map((c, idx) => <CandidateMini key={c.id} candidate={c} rank={idx + 1} onClick={() => { setSelectedCandidate?.(c); setPage('detail') }} />)}</div></Card> }
function CandidateMini({ candidate, rank, onClick }) { return <button onClick={onClick} className="w-full rounded-2xl border border-slate-200 p-4 text-left hover:bg-slate-50"><div className="flex items-start justify-between gap-3"><div className="flex items-start gap-3"><div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-slate-900 text-sm font-black text-white">{rank}</div><div><div className="flex flex-wrap items-center gap-2"><p className="text-sm font-black text-slate-900">{candidate.name}</p><Badge tone="blue">주재원 {candidate.expatFit}</Badge></div><p className="mt-1 text-xs font-semibold text-slate-500">{candidate.id} · {candidate.dept} · {candidate.position}</p><p className="mt-2 text-sm font-semibold text-slate-600">{candidate.strengths.join(' · ')}</p></div></div><ChevronRight className="h-4 w-4 text-slate-400" /></div></button> }
function RecentTemplatePanel({ setPage, canManage }) { return <Card><CardHeader icon={Filter} title="최근 사용 템플릿" subtitle="저장된 조건 즉시 적용" right={canManage ? <button onClick={() => setPage('templates')} className="rounded-xl bg-slate-900 px-3 py-2 text-xs font-black text-white">관리</button> : <Badge tone="amber">조회 권한</Badge>} /><div className="space-y-3 p-5">{templates.map((t) => <TemplateRow key={t.id} template={t} onApply={() => setPage('candidates')} />)}</div></Card> }
function TemplateRow({ template, onApply }) { return <div className="rounded-2xl border border-slate-200 p-4 hover:bg-slate-50"><div className="flex items-start justify-between gap-3"><div><div className="flex flex-wrap items-center gap-2"><p className="text-sm font-black text-slate-900">{template.name}</p><Badge tone={template.purpose === '주재원' ? 'blue' : 'amber'}>{template.purpose}</Badge></div><p className="mt-1 text-xs font-semibold text-slate-500">{template.scope} · 소유자 {template.owner}</p></div><div className="text-right"><p className="text-xl font-black text-slate-900">{template.count}</p><p className="text-xs font-bold text-slate-500">후보</p></div></div><div className="mt-3 flex justify-end"><button onClick={onApply} className="rounded-xl bg-slate-900 px-3 py-2 text-xs font-black text-white">적용</button></div></div> }
function UploadStatusPanel({ setPage, canManage }) { return <Card><CardHeader icon={Database} title="최근 업로드 및 데이터 상태" subtitle="후보자 마스터 기준일과 검증 결과" right={canManage && <button onClick={() => setPage?.('upload')} className="rounded-xl bg-slate-900 px-3 py-2 text-xs font-black text-white">새 업로드</button>} /><div className="overflow-x-auto"><table className="min-w-full divide-y divide-slate-200 text-sm"><thead className="bg-slate-50"><tr>{['파일명', '업로드', '행 수', '신규', '변경', '중복', '오류', '상태'].map((h) => <th key={h} className="px-5 py-3 text-left text-xs font-black uppercase tracking-wide text-slate-500">{h}</th>)}</tr></thead><tbody className="divide-y divide-slate-100 bg-white">{uploads.map((row) => <tr key={row.file} className="hover:bg-slate-50"><td className="min-w-64 px-5 py-4 font-black text-slate-900">{row.file}</td><td className="whitespace-nowrap px-5 py-4"><p className="font-bold text-slate-700">{row.at}</p><p className="text-xs font-semibold text-slate-500">{row.user}</p></td><td className="px-5 py-4 font-bold">{row.rows}</td><td className="px-5 py-4 font-bold text-blue-700">{row.newRows}</td><td className="px-5 py-4 font-bold text-amber-700">{row.changes}</td><td className="px-5 py-4 font-bold text-slate-600">{row.dup}</td><td className="px-5 py-4 font-bold text-rose-700">{row.errors}</td><td className="px-5 py-4"><Badge tone={row.errors > 0 ? 'red' : 'green'}>{row.status}</Badge></td></tr>)}</tbody></table></div></Card> }

function CandidatesPage({ setPage, setSelectedCandidate, selectedIds, setSelectedIds, candidateRows, apiStatus }) {
  const [query, setQuery] = useState('')
  const [purpose, setPurpose] = useState('전체')
  const [minLanguage, setMinLanguage] = useState(700)
  const [overseasOnly, setOverseasOnly] = useState(false)
  const filtered = useMemo(() => candidateRows.filter((c) => {
    const text = `${c.name} ${c.id} ${c.dept}`.toLowerCase().includes(query.toLowerCase())
    const purposeOk = purpose === '전체' || c.purpose.includes(purpose)
    const langOk = c.languageScore >= minLanguage
    const overseasOk = !overseasOnly || c.overseasMonths > 0
    return text && purposeOk && langOk && overseasOk
  }).sort((a, b) => b.expatFit - a.expatFit), [candidateRows, query, purpose, minLanguage, overseasOnly])
  const toggle = (id) => setSelectedIds((prev) => prev.includes(id) ? prev.filter((x) => x !== id) : prev.length >= 3 ? prev : [...prev, id])
  return <div className="grid grid-cols-1 gap-5 p-5 xl:grid-cols-[320px_minmax(0,1fr)]"><Card><CardHeader icon={Filter} title="필터 조건" subtitle="검색 결과에 실시간 반영" /><div className="space-y-4 p-5"><Select label="선별 목적" value={purpose} setValue={setPurpose} options={['전체', '주재원', '차기 팀장']} /><Range label={`최소 어학 점수 ${minLanguage}`} value={minLanguage} setValue={setMinLanguage} min={600} max={950} step={10} /><label className="flex items-center justify-between rounded-2xl bg-slate-50 p-3 text-sm font-bold text-slate-700 ring-1 ring-slate-200">해외 경험자만<input type="checkbox" checked={overseasOnly} onChange={(e) => setOverseasOnly(e.target.checked)} /></label><button className="w-full rounded-2xl bg-slate-900 px-4 py-3 text-sm font-black text-white">템플릿 저장</button></div></Card><Card className="overflow-hidden"><CardHeader icon={Users} title={`검색 결과 ${filtered.length}명`} subtitle={apiStatus} right={<div className="flex gap-2"><button disabled={selectedIds.length < 2} onClick={() => setPage('compare')} className="rounded-xl bg-slate-900 px-3 py-2 text-xs font-black text-white disabled:bg-slate-300">선택 비교</button><button className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-black text-slate-700">엑셀</button></div>} /><div className="border-b border-slate-100 p-5"><div className="relative"><Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-400" /><input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="이름, 사번, 부서 검색" className="h-11 w-full rounded-2xl border border-slate-200 bg-slate-50 pl-10 pr-4 text-sm font-semibold outline-none focus:border-slate-900 focus:bg-white" /></div></div><CandidateTable rows={filtered} toggle={toggle} selectedIds={selectedIds} setPage={setPage} setSelectedCandidate={setSelectedCandidate} /></Card></div>
}
function Select({ label, value, setValue, options }) { return <div><label className="mb-1.5 block text-xs font-black text-slate-600">{label}</label><select value={value} onChange={(e) => setValue(e.target.value)} className="h-11 w-full rounded-2xl border border-slate-200 bg-white px-3 text-sm font-black outline-none focus:border-slate-900">{options.map((o) => <option key={o}>{o}</option>)}</select></div> }
function Range({ label, value, setValue, min, max, step }) { return <div><label className="mb-1.5 block text-xs font-black text-slate-600">{label}</label><input type="range" min={min} max={max} step={step} value={value} onChange={(e) => setValue(Number(e.target.value))} className="w-full" /></div> }
function CandidateTable({ rows, selectedIds, toggle, setPage, setSelectedCandidate }) { return <div className="overflow-x-auto"><table className="min-w-full divide-y divide-slate-200 text-sm"><thead className="bg-slate-50"><tr>{['', '이름', '사번', '부서', '직위', '근속', '평가', '어학', '해외', '적합도', '상세'].map((h) => <th key={h} className="whitespace-nowrap px-4 py-3 text-left text-xs font-black uppercase tracking-wide text-slate-500">{h}</th>)}</tr></thead><tbody className="divide-y divide-slate-100 bg-white">{rows.map((c) => <tr key={c.id} className="hover:bg-slate-50"><td className="px-4 py-4"><input type="checkbox" checked={selectedIds.includes(c.id)} disabled={!selectedIds.includes(c.id) && selectedIds.length >= 3} onChange={() => toggle(c.id)} /></td><td className="whitespace-nowrap px-4 py-4 font-black text-slate-900">{c.name}</td><td className="whitespace-nowrap px-4 py-4 font-semibold text-slate-600">{c.id}</td><td className="whitespace-nowrap px-4 py-4 text-slate-700">{c.dept}</td><td className="whitespace-nowrap px-4 py-4 text-slate-700">{c.position}</td><td className="whitespace-nowrap px-4 py-4 text-slate-700">{c.tenure}년</td><td className="px-4 py-4"><Badge tone={String(c.performance || '').startsWith('A') ? 'green' : 'default'}>{c.performance}</Badge></td><td className="whitespace-nowrap px-4 py-4 text-slate-700">{c.language}</td><td className="whitespace-nowrap px-4 py-4 text-slate-700">{c.overseas}</td><td className="px-4 py-4 font-black text-slate-900">{c.expatFit}</td><td className="px-4 py-4"><button onClick={() => { setSelectedCandidate(c); setPage('detail') }} className="rounded-xl px-3 py-2 text-xs font-black text-slate-700 hover:bg-slate-200">상세</button></td></tr>)}</tbody></table></div> }

function DetailPage({ candidate, setPage, setSelectedIds }) {
  const c = candidate || candidates[0]
  const addCompare = () => setSelectedIds((prev) => prev.includes(c.id) ? prev : prev.length >= 3 ? prev : [...prev, c.id])
  return <div className="space-y-5 p-5"><div className="flex flex-wrap justify-between gap-3"><button onClick={() => setPage('candidates')} className="inline-flex items-center gap-2 rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-black text-slate-700"><ArrowLeft className="h-4 w-4" /> 목록으로</button><div className="flex gap-2"><button onClick={addCompare} className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-black text-white">비교 대상 추가</button><button className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-black text-slate-700">요약 내보내기</button></div></div><Card className="overflow-hidden"><div className="grid grid-cols-1 xl:grid-cols-[1.1fr_0.9fr]"><div className="p-6"><div className="flex items-center gap-5"><div className="flex h-24 w-24 items-center justify-center rounded-3xl bg-slate-900 text-3xl font-black text-white">{c.name[0]}</div><div><div className="flex flex-wrap items-center gap-2"><h2 className="text-3xl font-black tracking-tight">{c.name}</h2>{(c.purpose || []).map((p) => <Badge key={p} tone={p === '주재원' ? 'blue' : 'amber'}>{p}</Badge>)}</div><p className="mt-2 text-sm font-semibold text-slate-600">{c.id} · {c.dept} · {c.position} · 근속 {c.tenure}년</p></div></div></div><div className="border-t border-slate-100 bg-slate-50 p-6 xl:border-l xl:border-t-0"><div className="grid grid-cols-2 gap-3"><InfoBox label="주재원 적합도" value={c.expatFit} /><InfoBox label="팀장 적합도" value={c.leaderFit} /><InfoBox label="어학" value={c.language} /><InfoBox label="해외 경험" value={c.overseas} /></div></div></div></Card><div className="grid grid-cols-1 gap-4 md:grid-cols-4"><Metric label="최근 평가" value={c.performance} icon={Star} tone="green" /><Metric label="리더십" value={c.leadership} icon={ShieldCheck} tone="blue" /><Metric label="어학" value={c.language} icon={Globe2} /><Metric label="자격" value={c.certificate} icon={CheckCircle2} tone="amber" /></div><div className="grid grid-cols-1 gap-5 xl:grid-cols-2"><PanelList title="강점" icon={CheckCircle2} items={c.strengths || []} tone="green" /><PanelList title="확인 필요" icon={AlertTriangle} items={c.cautions || []} tone="amber" /></div><Card><CardHeader icon={BarChart3} title="평가/리더십 추이" subtitle="실제 구현 시 최근 3년 평가 추이와 항목별 리더십 차트 표시" /><div className="grid grid-cols-1 gap-4 p-5 md:grid-cols-5">{['2024 A', '2025 A', '2026 B+', '코칭 A', '실행력 A'].map((v) => <div key={v} className="rounded-2xl bg-slate-50 p-4 text-center ring-1 ring-slate-200"><p className="text-lg font-black text-slate-900">{v}</p></div>)}</div></Card></div>
}
function InfoBox({ label, value }) { return <div className="rounded-2xl bg-white p-4 ring-1 ring-slate-200"><p className="text-xs font-bold text-slate-500">{label}</p><p className="mt-1 text-lg font-black text-slate-900">{value}</p></div> }
function PanelList({ title, icon: Icon, items, tone }) { return <Card><CardHeader icon={Icon} title={title} /><div className="space-y-3 p-5">{items.map((item) => <div key={item} className={`rounded-2xl p-4 text-sm font-bold ring-1 ${tone === 'green' ? 'bg-emerald-50 text-emerald-800 ring-emerald-100' : 'bg-amber-50 text-amber-800 ring-amber-100'}`}>{item}</div>)}</div></Card> }

function ComparePage({ selectedIds, setPage, candidateRows }) {
  const selected = candidateRows.filter((c) => selectedIds.includes(c.id))
  const rows = selected.length >= 2 ? selected : candidateRows.slice(0, 3)
  const sorted = [...rows].sort((a, b) => b.expatFit - a.expatFit)
  return <div className="space-y-5 p-5"><div className="flex flex-wrap justify-between gap-3"><button onClick={() => setPage('candidates')} className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-black text-slate-700">후보 변경</button><button className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-black text-white">비교 요약 내보내기</button></div><div className="grid grid-cols-1 gap-4 xl:grid-cols-3">{rows.map((c) => <CompareCard key={c.id} c={c} top={c.id === sorted[0].id} />)}</div><Card><CardHeader icon={BarChart3} title="비교 매트릭스" subtitle="핵심 지표를 동일 기준으로 비교" /><div className="overflow-x-auto"><table className="min-w-full divide-y divide-slate-200 text-sm"><thead className="bg-slate-50"><tr><th className="px-5 py-3 text-left text-xs font-black text-slate-500">항목</th>{rows.map((c) => <th key={c.id} className="px-5 py-3 text-left text-xs font-black text-slate-500">{c.name}</th>)}</tr></thead><tbody className="divide-y divide-slate-100 bg-white">{['dept', 'position', 'performance', 'leadership', 'language', 'overseas', 'certificate', 'expatFit', 'leaderFit'].map((key) => <tr key={key}><td className="px-5 py-4 font-black text-slate-700">{labelOf(key)}</td>{rows.map((c) => <td key={`${c.id}-${key}`} className="px-5 py-4 font-semibold text-slate-700">{String(c[key])}</td>)}</tr>)}</tbody></table></div></Card></div>
}
function CompareCard({ c, top }) { return <div className={`rounded-3xl border p-5 ${top ? 'border-slate-900 bg-slate-900 text-white' : 'border-slate-200 bg-white'}`}><div className="flex items-center justify-between"><Badge tone={top ? 'amber' : 'default'}>{top ? '추천 1순위' : '비교 후보'}</Badge><p className="text-2xl font-black">{c.expatFit}</p></div><h3 className="mt-5 text-2xl font-black">{c.name}</h3><p className={`mt-1 text-sm font-semibold ${top ? 'text-white/70' : 'text-slate-500'}`}>{c.id} · {c.dept} · {c.position}</p><div className={`mt-5 space-y-2 text-sm font-semibold ${top ? 'text-white/70' : 'text-slate-600'}`}>{(c.strengths || []).map((s) => <p key={s}>· {s}</p>)}</div></div> }
function labelOf(key) { return { dept: '부서', position: '직위', performance: '평가', leadership: '리더십', language: '어학', overseas: '해외 경험', certificate: '자격', expatFit: '주재원 적합도', leaderFit: '팀장 적합도' }[key] || key }

function TemplatesPage({ setPage }) { return <div className="space-y-5 p-5"><div className="grid grid-cols-1 gap-4 md:grid-cols-4"><Metric label="전체 템플릿" value={templates.length} icon={Filter} /><Metric label="기본 제공" value="2" icon={Star} /><Metric label="공유 중" value="1" icon={Share2} /><Metric label="개인" value="1" icon={Lock} /></div><div className="grid grid-cols-1 gap-4 xl:grid-cols-2">{templates.map((t) => <TemplateCard key={t.id} t={t} setPage={setPage} />)}</div></div> }
function TemplateCard({ t, setPage }) { return <Card><div className="p-5"><div className="flex items-start justify-between gap-3"><div><div className="flex flex-wrap items-center gap-2"><h3 className="text-lg font-black text-slate-900">{t.name}</h3><Badge tone={t.purpose === '주재원' ? 'blue' : 'amber'}>{t.purpose}</Badge><Badge>{t.scope}</Badge></div><p className="mt-2 text-sm font-semibold text-slate-500">소유자 {t.owner} · 예상 후보 {t.count}명</p></div><button className="rounded-xl p-2 hover:bg-slate-100"><Settings2 className="h-5 w-5" /></button></div><div className="mt-4 flex flex-wrap gap-1.5">{t.filters.map((f) => <span key={f} className="rounded-full bg-slate-100 px-2.5 py-1 text-xs font-bold text-slate-600">{f}</span>)}</div><div className="mt-5 flex justify-end gap-2"><button className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-black text-slate-700"><Copy className="inline h-3.5 w-3.5" /> 복제</button><button className="rounded-xl border border-slate-200 bg-white px-3 py-2 text-xs font-black text-slate-700"><Share2 className="inline h-3.5 w-3.5" /> 공유</button><button onClick={() => setPage('candidates')} className="rounded-xl bg-slate-900 px-3 py-2 text-xs font-black text-white">적용</button></div></div></Card> }
function UploadPage({ onUploaded, lastUpload, setPage }) {
  const [file, setFile] = useState(null)
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)
  const apiReady = isApiEnabled()
  const activeStep = result?.upload_run_id ? 4 : result ? 3 : file ? 1 : 0
  const chooseFile = (nextFile) => {
    setFile(nextFile || null)
    setResult(null)
    setError('')
  }
  const runUpload = async (dryRun) => {
    if (!file) {
      setError('업로드할 xlsx 파일을 선택하세요.')
      return
    }
    setBusy(true)
    setError('')
    try {
      const payload = await uploadCandidateFile(file, { dryRun })
      setResult(payload)
      if (!dryRun) await onUploaded?.(payload)
    } catch (err) {
      setError(err.message)
    } finally {
      setBusy(false)
    }
  }

  return <div className="space-y-5 p-5"><Card><CardHeader icon={UploadCloud} title="엑셀 업로드 및 데이터 갱신" subtitle={apiReady ? "업로드 → 검증 → 최종 반영" : "API 주소가 설정되면 실제 업로드가 활성화됩니다."} /><div className="grid grid-cols-1 gap-4 p-5 md:grid-cols-5">{['파일 업로드', '파일 선택', '컬럼 확인', '검증 결과', '최종 반영'].map((s, i) => <div key={s} className={`rounded-2xl p-4 text-center ring-1 ${i <= activeStep ? 'bg-slate-900 text-white ring-slate-900' : 'bg-slate-50 text-slate-700 ring-slate-200'}`}><p className="text-xs font-black">STEP {i + 1}</p><p className="mt-1 text-sm font-black">{s}</p></div>)}</div><div className="p-5 pt-0"><label onDragOver={(e) => e.preventDefault()} onDrop={(e) => { e.preventDefault(); chooseFile(e.dataTransfer.files?.[0]) }} className="flex min-h-60 cursor-pointer flex-col items-center justify-center rounded-3xl border-2 border-dashed border-slate-300 bg-slate-50 p-8 text-center hover:bg-white"><FileSpreadsheet className="h-12 w-12 text-slate-500" /><h3 className="mt-4 text-xl font-black text-slate-900">{file ? file.name : '파일을 드래그하거나 클릭하여 업로드'}</h3><p className="mt-2 text-sm font-semibold text-slate-500">xlsx / 사번과 이름 필수 / dry run 검증 후 최종 반영</p><input type="file" accept=".xlsx" className="sr-only" onChange={(e) => chooseFile(e.target.files?.[0])} /></label>{!apiReady && <div className="mt-4 rounded-2xl bg-amber-50 p-4 text-sm font-bold text-amber-800 ring-1 ring-amber-100">`.env`에 `VITE_API_BASE_URL=http://127.0.0.1:5000`을 설정하고 프론트 서버를 다시 시작하면 실제 업로드를 사용할 수 있습니다.</div>}{error && <div className="mt-4 rounded-2xl bg-rose-50 p-4 text-sm font-bold text-rose-800 ring-1 ring-rose-100">{error}</div>}<div className="mt-5 flex flex-wrap justify-end gap-2"><button disabled={!apiReady || !file || busy} onClick={() => runUpload(true)} className="rounded-2xl border border-slate-200 bg-white px-5 py-3 text-sm font-black text-slate-700 disabled:bg-slate-100 disabled:text-slate-400">검증 실행</button><button disabled={!apiReady || !file || busy || !result || result.rows_error > 0} onClick={() => runUpload(false)} className="rounded-2xl bg-slate-900 px-5 py-3 text-sm font-black text-white disabled:bg-slate-300">최종 반영</button>{lastUpload && <button onClick={() => setPage('candidates')} className="rounded-2xl border border-slate-200 bg-white px-5 py-3 text-sm font-black text-slate-700">후보자 목록 보기</button>}</div></div></Card>{result && <Card><CardHeader icon={CheckCircle2} title="검증 결과" subtitle={result.file} right={<Badge tone={result.rows_error > 0 ? 'red' : 'green'}>{result.dry_run ? '검증 완료' : '반영 완료'}</Badge>} /><div className="grid grid-cols-1 gap-4 p-5 md:grid-cols-3 xl:grid-cols-6"><Metric label="정상 행" value={result.rows_valid} icon={CheckCircle2} tone="green" /><Metric label="신규" value={result.newRows ?? 0} icon={User} tone="blue" /><Metric label="변경" value={result.changedRows ?? 0} icon={Activity} tone="amber" /><Metric label="중복" value={result.dup ?? 0} icon={Copy} /><Metric label="오류 행" value={result.rows_error} icon={AlertTriangle} tone={result.rows_error > 0 ? 'red' : 'default'} /><Metric label="반영 건수" value={result.upserted ?? '-'} icon={Database} tone="purple" /></div>{result.headers?.length > 0 && <div className="px-5 pb-5"><p className="mb-2 text-xs font-black text-slate-500">인식된 컬럼</p><div className="flex flex-wrap gap-2">{result.headers.map((header) => <span key={header} className="rounded-full bg-slate-100 px-3 py-1 text-xs font-bold text-slate-600">{header || '(빈 컬럼)'}</span>)}</div></div>}{result.errors?.length > 0 && <div className="px-5 pb-5"><div className="overflow-x-auto rounded-2xl border border-slate-200"><table className="min-w-full divide-y divide-slate-200 text-sm"><thead className="bg-slate-50"><tr><th className="px-4 py-3 text-left text-xs font-black text-slate-500">행</th><th className="px-4 py-3 text-left text-xs font-black text-slate-500">오류</th></tr></thead><tbody className="divide-y divide-slate-100 bg-white">{result.errors.map((item) => <tr key={`${item.row_number}-${item.message}`}><td className="px-4 py-3 font-bold">{item.row_number}</td><td className="px-4 py-3 font-semibold text-rose-700">{item.message}</td></tr>)}</tbody></table></div></div>}</Card>}<UploadStatusPanel canManage /></div>
}
function AuditPage() { return <div className="space-y-5 p-5"><div className="grid grid-cols-1 gap-4 md:grid-cols-4"><Metric label="상세 조회" value="42" icon={Eye} tone="green" /><Metric label="다운로드" value="7" icon={Download} tone="amber" /><Metric label="업로드" value="3" icon={UploadCloud} tone="blue" /><Metric label="차단" value="1" icon={ShieldAlert} tone="red" /></div><Card><CardHeader icon={Activity} title="감사 로그" subtitle="조회·다운로드·업로드·권한 차단 이벤트" right={<button className="rounded-xl bg-slate-900 px-3 py-2 text-xs font-black text-white">엑셀 내보내기</button>} /><div className="overflow-x-auto"><table className="min-w-full divide-y divide-slate-200 text-sm"><thead className="bg-slate-50"><tr>{['일시', '사용자', '권한', '작업', '대상', '결과', '위험도', 'IP'].map((h) => <th key={h} className="px-5 py-3 text-left text-xs font-black text-slate-500">{h}</th>)}</tr></thead><tbody className="divide-y divide-slate-100 bg-white">{audits.map((a) => <tr key={`${a.time}-${a.action}`} className="hover:bg-slate-50"><td className="whitespace-nowrap px-5 py-4 font-bold text-slate-700">{a.time}</td><td className="whitespace-nowrap px-5 py-4 font-black text-slate-900">{a.user}</td><td className="whitespace-nowrap px-5 py-4 text-slate-600">{a.role}</td><td className="whitespace-nowrap px-5 py-4 font-bold text-slate-700">{a.action}</td><td className="min-w-56 px-5 py-4 text-slate-600">{a.target}</td><td className="px-5 py-4"><Badge tone={a.result === '차단' ? 'red' : 'green'}>{a.result}</Badge></td><td className="px-5 py-4"><Badge tone={a.risk === '위험' ? 'red' : a.risk === '주의' ? 'amber' : 'green'}>{a.risk}</Badge></td><td className="whitespace-nowrap px-5 py-4 text-slate-600">{a.ip}</td></tr>)}</tbody></table></div></Card></div> }
function ForbiddenPage({ setPage, role }) { return <div className="flex min-h-[calc(100vh-88px)] items-center justify-center p-6"><Card className="w-full max-w-3xl overflow-hidden"><div className="grid grid-cols-1 xl:grid-cols-[0.85fr_1.15fr]"><div className="bg-slate-950 p-8 text-white"><div className="flex h-16 w-16 items-center justify-center rounded-3xl bg-rose-500/15 text-rose-300"><ShieldAlert className="h-9 w-9" /></div><h2 className="mt-8 text-4xl font-black tracking-tight">접근 권한이 없습니다.</h2><p className="mt-4 text-sm font-semibold leading-7 text-white/65">현재 권한으로 요청한 화면에 접근할 수 없습니다. 차단 이벤트는 감사 로그에 기록됩니다.</p></div><div className="p-8"><div className="flex flex-wrap gap-2"><Badge tone="red">403 Forbidden</Badge><Badge tone="amber">현재 권한: {role === 'hr' ? '인사담당자' : '팀장/조회자'}</Badge></div><div className="mt-6 space-y-3"><StatusRow label="요청 경로" value="/restricted" /><StatusRow label="필요 권한" value="인사담당자" /><StatusRow label="처리 방식" value="메뉴 숨김 + 서버 차단" /></div><div className="mt-6 flex justify-end gap-2"><button onClick={() => setPage('dashboard')} className="rounded-xl border border-slate-200 bg-white px-4 py-2 text-sm font-black text-slate-700"><Home className="inline h-4 w-4" /> 홈으로</button><button onClick={() => setPage('audit')} className="rounded-xl bg-slate-900 px-4 py-2 text-sm font-black text-white">감사 로그</button></div></div></div></Card></div> }

export default function App() {
  const [authed, setAuthed] = useState(false)
  const [role, setRole] = useState('hr')
  const [page, setPage] = useState('login')
  const [candidateRows, setCandidateRows] = useState(candidates)
  const [apiStatus, setApiStatus] = useState(isApiEnabled() ? 'API 후보자 데이터를 조회합니다.' : 'API 주소 미설정: mock data를 표시합니다.')
  const [lastUpload, setLastUpload] = useState(null)
  const [selectedCandidate, setSelectedCandidate] = useState(candidates[0])
  const [selectedIds, setSelectedIds] = useState(['E24017', 'E21884', 'E22615'])

  const reloadCandidates = async () => {
    if (!isApiEnabled()) return
    try {
      const rows = await fetchCandidateRows()
      if (rows.length) {
        setCandidateRows(rows)
        setSelectedCandidate((current) => rows.find((row) => row.id === current?.id) || rows[0])
        setSelectedIds((current) => current.filter((id) => rows.some((row) => row.id === id)))
        setApiStatus(`API 연동: 후보자 ${rows.length}명`)
      } else {
        setApiStatus('API 연동: 저장된 후보자가 없어 mock data를 표시합니다.')
      }
    } catch (err) {
      setApiStatus(`API 오류: ${err.message}`)
    }
  }

  useEffect(() => {
    reloadCandidates()
  }, [])

  const handleUploaded = async (summary) => {
    setLastUpload(summary)
    await reloadCandidates()
  }

  if (!authed || page === 'login') return <LoginPage setAuthed={setAuthed} setPage={setPage} role={role} setRole={setRole} />
  let content
  if (page === 'dashboard') content = <DashboardPage setPage={setPage} role={role} candidateRows={candidateRows} setSelectedCandidate={setSelectedCandidate} />
  else if (page === 'candidates') content = <CandidatesPage setPage={setPage} setSelectedCandidate={setSelectedCandidate} selectedIds={selectedIds} setSelectedIds={setSelectedIds} candidateRows={candidateRows} apiStatus={apiStatus} />
  else if (page === 'detail') content = <DetailPage candidate={selectedCandidate} setPage={setPage} setSelectedIds={setSelectedIds} />
  else if (page === 'compare') content = <ComparePage selectedIds={selectedIds} setPage={setPage} candidateRows={candidateRows} />
  else if (page === 'templates') content = <TemplatesPage setPage={setPage} />
  else if (page === 'upload') content = <UploadPage onUploaded={handleUploaded} lastUpload={lastUpload} setPage={setPage} />
  else if (page === 'audit') content = <AuditPage />
  else content = <ForbiddenPage setPage={setPage} role={role} />
  return <AppShell role={role} setRole={setRole} page={page} setPage={setPage}>{content}</AppShell>
}
