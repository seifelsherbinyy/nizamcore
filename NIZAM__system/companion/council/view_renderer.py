from __future__ import annotations

import html
import uuid
from datetime import datetime, timezone

from .contracts import CouncilVerdict, CouncilView


def _utc_now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _vote_rows(verdict: CouncilVerdict) -> tuple[tuple[str, str, float], ...]:
    return tuple((vote.agent, vote.ballot, vote.weight) for vote in verdict.votes)


def render_markdown(verdict: CouncilVerdict, *, motion_title: str) -> CouncilView:
    lines = [
        f"# Council verdict — {motion_title}",
        "",
        f"**Outcome:** {verdict.outcome}",
        f"**Protocol:** {verdict.protocol_used}",
        f"**Rounds:** {verdict.rounds_completed}",
        "",
        "## Vote table",
        "| Agent | Ballot | Weight |",
        "| --- | --- | ---: |",
    ]
    for agent, ballot, weight in _vote_rows(verdict):
        lines.append(f"| {agent} | {ballot} | {weight:.2f} |")
    if verdict.judge_synthesis:
        lines.extend(["", "## Judge synthesis", verdict.judge_synthesis])
    if verdict.dissent:
        lines.extend(["", "## Dissent"])
        lines.extend(f"- {line}" for line in verdict.dissent)
    body = "\n".join(lines)
    return CouncilView(
        view_id=str(uuid.uuid4()),
        verdict_id=verdict.verdict_id,
        motion_title=motion_title,
        format="markdown",
        body=body,
        vote_table=_vote_rows(verdict),
        dissent_lines=verdict.dissent,
        created_at=_utc_now(),
    )


def render_html(verdict: CouncilVerdict, *, motion_title: str) -> CouncilView:
    rows = []
    for agent, ballot, weight in _vote_rows(verdict):
        rows.append(
            "<tr>"
            f"<td>{html.escape(agent)}</td>"
            f"<td>{html.escape(ballot)}</td>"
            f"<td>{weight:.2f}</td>"
            "</tr>"
        )
    dissent_html = "".join(f"<li>{html.escape(line)}</li>" for line in verdict.dissent)
    synthesis = (
        f"<p><strong>Judge synthesis:</strong> {html.escape(verdict.judge_synthesis)}</p>"
        if verdict.judge_synthesis
        else ""
    )
    body = (
        f"<h1>Council verdict — {html.escape(motion_title)}</h1>"
        f"<p><strong>Outcome:</strong> {html.escape(verdict.outcome)}</p>"
        f"<p><strong>Protocol:</strong> {html.escape(verdict.protocol_used)}</p>"
        "<table><thead><tr><th>Agent</th><th>Ballot</th><th>Weight</th></tr></thead>"
        f"<tbody>{''.join(rows)}</tbody></table>"
        f"{synthesis}"
        f"<ul>{dissent_html}</ul>"
    )
    return CouncilView(
        view_id=str(uuid.uuid4()),
        verdict_id=verdict.verdict_id,
        motion_title=motion_title,
        format="html",
        body=body,
        vote_table=_vote_rows(verdict),
        dissent_lines=verdict.dissent,
        created_at=_utc_now(),
    )


def render_telegram_compact(verdict: CouncilVerdict, *, motion_title: str) -> CouncilView:
    vote_bits = [
        f"{agent}:{ballot}"
        for agent, ballot, _weight in _vote_rows(verdict)
    ]
    dissent = "; ".join(verdict.dissent[:3])
    body = (
        f"Council · {motion_title}\n"
        f"{verdict.outcome} via {verdict.protocol_used}\n"
        f"Votes: {', '.join(vote_bits)}"
    )
    if dissent:
        body += f"\nDissent: {dissent}"
    return CouncilView(
        view_id=str(uuid.uuid4()),
        verdict_id=verdict.verdict_id,
        motion_title=motion_title,
        format="telegram_compact",
        body=body,
        vote_table=_vote_rows(verdict),
        dissent_lines=verdict.dissent,
        created_at=_utc_now(),
    )


def render_view(
    verdict: CouncilVerdict,
    *,
    motion_title: str,
    format: str = "markdown",
) -> CouncilView:
    if format == "html":
        return render_html(verdict, motion_title=motion_title)
    if format == "telegram_compact":
        return render_telegram_compact(verdict, motion_title=motion_title)
    return render_markdown(verdict, motion_title=motion_title)
