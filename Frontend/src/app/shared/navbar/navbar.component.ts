import { Component, inject, signal } from '@angular/core';
import { Router, RouterLink, RouterLinkActive } from '@angular/router';
import { finalize } from 'rxjs';

import { AuthService } from '../../core/auth/auth.service';

@Component({
  selector: 'app-navbar',
  standalone: true,
  imports: [RouterLink, RouterLinkActive],
  templateUrl: './navbar.component.html',
  styleUrls: ['./navbar.component.scss']
})
export class NavbarComponent {
  protected readonly auth = inject(AuthService);
  private readonly router = inject(Router);
  protected readonly loggingOut = signal(false);

  protected dashboardLink(): string {
    return this.auth.defaultAuthenticatedRoute();
  }

  protected isAdmin(): boolean {
    return this.auth.federationContext().userRole === 'ADMIN';
  }

  protected isCoach(): boolean {
    return this.auth.federationContext().federationRole === 'COA';
  }

  protected isManager(): boolean {
    return this.auth.federationContext().federationRole === 'MGR';
  }

  protected isReferee(): boolean {
    return this.auth.federationContext().federationRole === 'REF';
  }

  protected canSeeCompetitions(): boolean {
    return this.auth.isAuthenticated();
  }

  protected canSeeAthletes(): boolean {
    return this.isAdmin() || this.isCoach() || this.isManager();
  }

  protected canSeeTeams(): boolean {
    return this.isAdmin();
  }

  protected canSeePools(): boolean {
    return this.isAdmin() || this.isManager();
  }

  protected logout(): void {
    this.loggingOut.set(true);

    this.auth
      .logout()
      .pipe(finalize(() => this.loggingOut.set(false)))
      .subscribe({
        next: () => void this.router.navigateByUrl('/login'),
        error: () => void this.router.navigateByUrl('/login')
      });
  }
}