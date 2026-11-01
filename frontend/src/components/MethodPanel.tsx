/** How every number on the page is worked out, in plain words (CX3, CX5). */
export function MethodPanel() {
  return (
    <section className="method" aria-labelledby="method-heading">
      <h2 id="method-heading" className="section-title">
        How this is calculated
      </h2>
      <details className="method__details">
        <summary>The rules, assumptions and limits</summary>
        <dl>
          <div>
            <dt>Decision time</dt>
            <dd>
              You buy on the day before delivery. The default is 09:00 London time, which is an
              assumption to confirm; any forecast run on the timeline can be chosen instead.
            </dd>
          </div>
          <div>
            <dt>Which forecast</dt>
            <dd>
              For each hour, the newest forecast published at or before the decision time. Anything
              published later is never used, however close it was.
            </dd>
          </div>
          <div>
            <dt>Actual wind</dt>
            <dd>
              Metered wind generation is reported every half hour. An hour’s actual is the average of
              its two half hours; if either is missing the hour is left out, not guessed.
            </dd>
          </div>
          <div>
            <dt>Miss</dt>
            <dd>
              Forecast minus actual, in MW. Positive means the forecast was too high, the risky
              direction for a buyer.
            </dd>
          </div>
          <div>
            <dt>Safety margin</dt>
            <dd>
              In 9 in 10 (or 19 in 20) past hours, the forecast was no more than this much too high.
              Only hours that had finished by the decision time count, and at least 72 of them are
              needed. Plan for = forecast minus margin.
            </dd>
          </div>
          <div>
            <dt>Margin held</dt>
            <dd>
              Each day of January replayed with the margin known that morning: the share of hours
              where actual wind was at least the plan-for level.
            </dd>
          </div>
          <div>
            <dt>Limits</dt>
            <dd>
              National GB wind only, January 2026 only. The forecast ran high on average all month;
              the cause is not established, and one possibility is that the two datasets do not count
              exactly the same wind. In January London time equals UTC, so clock changes are not
              tested here.
            </dd>
          </div>
          <div>
            <dt>Data</dt>
            <dd>
              Elexon BMRS: FUELHH (wind generation outturn) and WINDFOR (day-ahead wind forecast),
              checked against a manifest of row counts and checksums.
            </dd>
          </div>
        </dl>
      </details>
    </section>
  );
}
