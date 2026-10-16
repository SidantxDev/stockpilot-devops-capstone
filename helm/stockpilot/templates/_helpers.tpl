{{- define "stockpilot.name" -}}
{{- .Chart.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "stockpilot.fullname" -}}
{{- if contains .Chart.Name .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name .Chart.Name | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}

{{- define "stockpilot.labels" -}}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" }}
app.kubernetes.io/part-of: stockpilot
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end -}}

{{/* Selector labels for one component: include with (dict "ctx" $ "component" "backend") */}}
{{- define "stockpilot.selectorLabels" -}}
app.kubernetes.io/name: {{ include "stockpilot.name" .ctx }}
app.kubernetes.io/instance: {{ .ctx.Release.Name }}
app.kubernetes.io/component: {{ .component }}
{{- end -}}

{{- define "stockpilot.componentLabels" -}}
{{ include "stockpilot.labels" .ctx }}
{{ include "stockpilot.selectorLabels" . }}
{{- end -}}

{{- define "stockpilot.backendName" -}}{{ include "stockpilot.fullname" . }}-backend{{- end -}}
{{- define "stockpilot.frontendName" -}}{{ include "stockpilot.fullname" . }}-frontend{{- end -}}
{{- define "stockpilot.postgresName" -}}{{ include "stockpilot.fullname" . }}-postgres{{- end -}}

{{- define "stockpilot.postgresSecret" -}}
{{- if .Values.postgres.existingSecret -}}
{{- .Values.postgres.existingSecret -}}
{{- else -}}
{{- include "stockpilot.postgresName" . -}}
{{- end -}}
{{- end -}}

{{- define "stockpilot.podSecurityContext" -}}
runAsNonRoot: true
seccompProfile:
  type: RuntimeDefault
{{- end -}}

{{- define "stockpilot.containerSecurityContext" -}}
allowPrivilegeEscalation: false
readOnlyRootFilesystem: true
capabilities:
  drop: ["ALL"]
{{- end -}}
