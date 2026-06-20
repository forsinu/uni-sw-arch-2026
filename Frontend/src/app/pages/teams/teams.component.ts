import { Component, inject, signal } from '@angular/core';
import { FormBuilder, ReactiveFormsModule, Validators } from '@angular/forms';
import { FederationApiService } from '../../Services/FederationService/api/federation-api.service';
import { SwimmingTeam } from '../../Services/FederationService/api/federation-api.models';
import { AuthService } from '../../core/auth/auth.service';

@Component({ selector: 'app-teams', standalone: true, imports: [ReactiveFormsModule], templateUrl: './teams.component.html', styleUrls: ['./teams.component.scss'] })
export class TeamsComponent {
  private readonly api = inject(FederationApiService);
  private readonly fb = inject(FormBuilder);
  private readonly auth = inject(AuthService);
  protected readonly teams = signal<SwimmingTeam[]>([]);
  protected readonly loading = signal(true);
  protected readonly saving = signal(false);
  protected readonly error = signal<string | null>(null);
  protected readonly actionMessage = signal<string | null>(null);
  protected readonly actionError = signal<string | null>(null);
  protected readonly form = this.fb.nonNullable.group({ name: ['', [Validators.required, Validators.minLength(2)]], shortName: [''] });
  constructor() { this.reload(); }
  protected canManage(): boolean { return this.auth.federationContext().userRole === 'ADMIN'; }
  protected createTeam(): void {
    if (this.form.invalid) { this.form.markAllAsTouched(); return; }
    const value = this.form.getRawValue(); this.saving.set(true); this.actionError.set(null); this.actionMessage.set(null);
    this.api.createTeam({ name: value.name.trim(), shortName: value.shortName.trim() || null }).subscribe({
      next: () => { this.actionMessage.set('Team created.'); this.form.reset({ name: '', shortName: '' }); this.saving.set(false); this.reload(); },
      error: (error) => { this.actionError.set(this.auth.getErrorMessage(error, 'Unable to create team.')); this.saving.set(false); }
    });
  }
  protected deactivateTeam(team: SwimmingTeam): void {
    this.saving.set(true); this.actionError.set(null); this.actionMessage.set(null);
    this.api.deactivateTeam(team.id).subscribe({
      next: () => { this.actionMessage.set(`Team ${team.name} deactivated.`); this.saving.set(false); this.reload(); },
      error: (error) => { this.actionError.set(this.auth.getErrorMessage(error, 'Unable to deactivate team.')); this.saving.set(false); }
    });
  }
  private reload(): void { this.api.listTeams().subscribe({ next: (teams) => { this.teams.set(teams); this.loading.set(false); }, error: (error) => { this.error.set(this.auth.getErrorMessage(error, 'Unable to load teams.')); this.loading.set(false); } }); }
}