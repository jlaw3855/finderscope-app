/** Seeded star field, Milky Way bias, and arced shooting stars for the sky layer. */

const STAR_COUNT = 720;
const STAR_SEED = 42;
const VIEW_WIDTH = 1000;
const VIEW_HEIGHT = 600;
const UPPER_SKY_Y = VIEW_HEIGHT * 0.45;
const UPPER_SKY_BIAS = 1.4;

const MOON_CX = 872;
const MOON_CY = 88;
const MOON_EXCLUSION_RADIUS = 105;

const MILKY_WAY_CX = 500;
const MILKY_WAY_CY = 300;
const MILKY_WAY_ANGLE_RAD = (32 * Math.PI) / 180;
const MILKY_WAY_HALF_LENGTH = 920;
const MILKY_WAY_HALF_WIDTH = 85;
const MILKY_WAY_STAR_BIAS = 0.45;

const METEOR_ARC_DX = 840;
const METEOR_ARC_DY = 504;
const METEOR_CTRL_BULGE = -36;
const METEOR_BASE_TRAIL_LENGTH = 340;
const METEOR_DURATION_MS = 1120;
const METEOR_SCALE_MIN = 0.8;
const METEOR_SCALE_MAX = 1.2;
const METEOR_UPPER_BIAS = 1.4;
const METEOR_MIN_INTERVAL_MS = 10000;
const METEOR_MAX_INTERVAL_MS = 14000;
const METEOR_TRAIL_SAMPLES = 14;
const METEOR_TRAIL_PEAK_COLOR = 'rgba(220, 235, 255, 0.42)';
const METEOR_FADE_IN_MS = 80;

const SVG_NS = 'http://www.w3.org/2000/svg';

type RandFn = () => number;

let meteorIdCounter = 0;

/** Seeded PRNG for reproducible star placement in visual baselines. */
function mulberry32(seed: number): RandFn {
  let state = seed;
  return () => {
    state += 0x6d2b79f5;
    let t = state;
    t = Math.imul(t ^ (t >>> 15), t | 1);
    t ^= t + Math.imul(t ^ (t >>> 7), t | 61);
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
  };
}

function randRange(rand: RandFn, min: number, max: number): number {
  return min + rand() * (max - min);
}

function isInsideMoon(cx: number, cy: number): boolean {
  const dx = cx - MOON_CX;
  const dy = cy - MOON_CY;
  return dx * dx + dy * dy <= MOON_EXCLUSION_RADIUS * MOON_EXCLUSION_RADIUS;
}

function distanceToMilkyBand(x: number, y: number): number {
  const dx = x - MILKY_WAY_CX;
  const dy = y - MILKY_WAY_CY;
  const sinAngle = Math.sin(MILKY_WAY_ANGLE_RAD);
  const cosAngle = Math.cos(MILKY_WAY_ANGLE_RAD);
  return Math.abs(-dx * sinAngle + dy * cosAngle);
}

function sampleMilkyWayStar(rand: RandFn): { cx: number; cy: number } {
  const along = randRange(rand, -MILKY_WAY_HALF_LENGTH, MILKY_WAY_HALF_LENGTH);
  const perp = randRange(rand, -MILKY_WAY_HALF_WIDTH, MILKY_WAY_HALF_WIDTH);
  const sinAngle = Math.sin(MILKY_WAY_ANGLE_RAD);
  const cosAngle = Math.cos(MILKY_WAY_ANGLE_RAD);

  return {
    cx: MILKY_WAY_CX + along * cosAngle - perp * sinAngle,
    cy: MILKY_WAY_CY + along * sinAngle + perp * cosAngle,
  };
}

function sampleGeneralSkyStar(rand: RandFn, upperPick: number): { cx: number; cy: number } {
  return {
    cx: rand() * VIEW_WIDTH,
    cy:
      rand() < upperPick
        ? rand() * UPPER_SKY_Y
        : UPPER_SKY_Y + rand() * (VIEW_HEIGHT - UPPER_SKY_Y),
  };
}

function buildStarField(container: SVGGElement): void {
  const rand = mulberry32(STAR_SEED);
  const upperWeight = UPPER_SKY_Y * UPPER_SKY_BIAS;
  const lowerWeight = VIEW_HEIGHT - UPPER_SKY_Y;
  const upperPick = upperWeight / (upperWeight + lowerWeight);

  const fragment = document.createDocumentFragment();
  let placed = 0;

  while (placed < STAR_COUNT) {
    const inBand = rand() < MILKY_WAY_STAR_BIAS;
    const { cx, cy } = inBand
      ? sampleMilkyWayStar(rand)
      : sampleGeneralSkyStar(rand, upperPick);

    if (
      cx < 0
      || cx > VIEW_WIDTH
      || cy < 0
      || cy > VIEW_HEIGHT
      || isInsideMoon(cx, cy)
    ) {
      continue;
    }

    const isBright = rand() < (inBand ? 0.1 : 0.08);
    const r = randRange(rand, 0.4, isBright ? 1.1 : 0.85);
    const bandBoost =
      inBand && distanceToMilkyBand(cx, cy) < MILKY_WAY_HALF_WIDTH * 0.5 ? 0.08 : 0;
    const opacity = isBright
      ? randRange(rand, 0.6, 0.75)
      : randRange(rand, 0.22 + bandBoost, 0.55 + bandBoost);

    const circle = document.createElementNS(SVG_NS, 'circle');
    circle.setAttribute('cx', cx.toFixed(2));
    circle.setAttribute('cy', cy.toFixed(2));
    circle.setAttribute('r', r.toFixed(2));
    circle.setAttribute('opacity', Math.min(opacity, 0.85).toFixed(2));
    fragment.appendChild(circle);
    placed += 1;
  }

  container.replaceChildren(fragment);
}

function randomMeteorScale(): number {
  return randRange(Math.random, METEOR_SCALE_MIN, METEOR_SCALE_MAX);
}

function meteorPathD(startX: number, startY: number, scale: number): string {
  const dx = METEOR_ARC_DX * scale;
  const dy = METEOR_ARC_DY * scale;
  const bulge = METEOR_CTRL_BULGE * scale;
  const endX = startX + dx;
  const endY = startY + dy;
  const ctrlX = startX + dx * 0.5;
  const ctrlY = startY + dy * 0.5 + bulge;
  return `M ${startX} ${startY} Q ${ctrlX} ${ctrlY} ${endX} ${endY}`;
}

function meteorDurationMs(scale: number): number {
  return Math.round(METEOR_DURATION_MS * scale);
}

function randomMeteorStart(): { x: number; y: number } {
  const width = window.innerWidth;
  const height = window.innerHeight;
  const midY = height * 0.5;
  const upperWeight = midY * METEOR_UPPER_BIAS;
  const lowerWeight = height - midY;
  const upperPick = upperWeight / (upperWeight + lowerWeight);

  return {
    x: width * randRange(Math.random, 0.04, 0.96),
    y:
      Math.random() < upperPick
        ? height * randRange(Math.random, 0.03, 0.5)
        : height * randRange(Math.random, 0.5, 0.97),
  };
}

function meteorFadeOpacity(elapsedMs: number, durationMs: number): number {
  if (elapsedMs < METEOR_FADE_IN_MS) {
    return elapsedMs / METEOR_FADE_IN_MS;
  }

  const fadeOutStart = durationMs * 0.88;
  if (elapsedMs > fadeOutStart) {
    return Math.max(0, (durationMs - elapsedMs) / (durationMs - fadeOutStart));
  }

  return 1;
}

function meteorTrailLengthScale(elapsedMs: number): number {
  return Math.min(1, elapsedMs / METEOR_FADE_IN_MS);
}

function samplePathSegment(
  arcProbe: SVGPathElement,
  startDistance: number,
  endDistance: number,
  segments: number,
): DOMPoint[] {
  const points: DOMPoint[] = [];
  if (endDistance <= startDistance) {
    return points;
  }

  for (let index = 0; index <= segments; index += 1) {
    const distance = startDistance + (endDistance - startDistance) * (index / segments);
    points.push(arcProbe.getPointAtLength(distance));
  }

  return points;
}

function polylinePathD(points: DOMPoint[]): string {
  if (points.length === 0) {
    return '';
  }

  return points
    .map((point, index) => {
      const command = index === 0 ? 'M' : 'L';
      return `${command} ${point.x.toFixed(2)} ${point.y.toFixed(2)}`;
    })
    .join(' ');
}

function createTrailGradient(defs: SVGDefsElement, gradientId: string): SVGLinearGradientElement {
  const gradient = document.createElementNS(SVG_NS, 'linearGradient');
  gradient.setAttribute('id', gradientId);
  gradient.setAttribute('gradientUnits', 'userSpaceOnUse');

  const stopTail = document.createElementNS(SVG_NS, 'stop');
  stopTail.setAttribute('offset', '0%');
  stopTail.setAttribute('stop-color', 'rgba(220, 235, 255, 0)');

  const stopFade = document.createElementNS(SVG_NS, 'stop');
  stopFade.setAttribute('offset', '35%');
  stopFade.setAttribute('stop-color', 'rgba(220, 235, 255, 0.08)');

  const stopMid = document.createElementNS(SVG_NS, 'stop');
  stopMid.setAttribute('offset', '50%');
  stopMid.setAttribute('stop-color', METEOR_TRAIL_PEAK_COLOR);

  const stopHead = document.createElementNS(SVG_NS, 'stop');
  stopHead.setAttribute('offset', '100%');
  stopHead.setAttribute('stop-color', METEOR_TRAIL_PEAK_COLOR);

  gradient.append(stopTail, stopFade, stopMid, stopHead);
  defs.appendChild(gradient);
  return gradient;
}

function updateTrailGradient(
  gradient: SVGLinearGradientElement,
  tailPoint: DOMPoint,
  headPoint: DOMPoint,
): void {
  gradient.setAttribute('x1', String(tailPoint.x));
  gradient.setAttribute('y1', String(tailPoint.y));
  gradient.setAttribute('x2', String(headPoint.x));
  gradient.setAttribute('y2', String(headPoint.y));
}

function animateMeteor(
  svg: SVGSVGElement,
  arcProbe: SVGPathElement,
  trail: SVGPathElement,
  trailGradient: SVGLinearGradientElement,
  head: SVGCircleElement,
  pathLength: number,
  trailLength: number,
  durationMs: number,
): () => void {
  const startTime = performance.now();
  let frameId = 0;

  const frame = (now: number) => {
    const elapsedMs = now - startTime;
    const progress = Math.min(elapsedMs / durationMs, 1);
    const headDistance = Math.min(Math.max(progress * pathLength, 0), pathLength);
    const effectiveTrailLength = trailLength * meteorTrailLengthScale(elapsedMs);
    const tailDistance = Math.max(0, headDistance - effectiveTrailLength);
    const opacity = meteorFadeOpacity(elapsedMs, durationMs);
    const segmentPoints = samplePathSegment(
      arcProbe,
      tailDistance,
      headDistance,
      METEOR_TRAIL_SAMPLES,
    );

    trail.setAttribute('d', polylinePathD(segmentPoints));
    trail.style.opacity = String(opacity);

    if (segmentPoints.length >= 2) {
      updateTrailGradient(
        trailGradient,
        segmentPoints[0],
        segmentPoints[segmentPoints.length - 1],
      );
      const tip = segmentPoints[segmentPoints.length - 1];
      head.setAttribute('cx', tip.x.toFixed(2));
      head.setAttribute('cy', tip.y.toFixed(2));
    }

    head.style.opacity = String(opacity);

    if (progress < 1) {
      frameId = window.requestAnimationFrame(frame);
      return;
    }

    svg.remove();
  };

  frameId = window.requestAnimationFrame(frame);

  return () => {
    window.cancelAnimationFrame(frameId);
  };
}

function spawnMeteor(scene: HTMLElement): void {
  const { x, y } = randomMeteorStart();
  const scale = randomMeteorScale();
  const pathD = meteorPathD(x, y, scale);
  const durationMs = meteorDurationMs(scale);

  const svg = document.createElementNS(SVG_NS, 'svg');
  svg.setAttribute('class', 'shooting-star');
  svg.setAttribute('width', String(window.innerWidth));
  svg.setAttribute('height', String(window.innerHeight));
  svg.setAttribute('viewBox', `0 0 ${window.innerWidth} ${window.innerHeight}`);
  svg.setAttribute('aria-hidden', 'true');

  const arcProbe = document.createElementNS(SVG_NS, 'path');
  arcProbe.setAttribute('d', pathD);
  arcProbe.setAttribute('visibility', 'hidden');

  const pathLength = arcProbe.getTotalLength();
  const trailLength = Math.min(METEOR_BASE_TRAIL_LENGTH * scale, pathLength * 0.45);

  const defs = document.createElementNS(SVG_NS, 'defs');
  const gradientId = `meteor-trail-grad-${meteorIdCounter}`;
  meteorIdCounter += 1;
  const trailGradient = createTrailGradient(defs, gradientId);

  const trail = document.createElementNS(SVG_NS, 'path');
  trail.setAttribute('class', 'shooting-star-trail');
  trail.setAttribute('stroke', `url(#${gradientId})`);
  trail.style.opacity = '0';

  const head = document.createElementNS(SVG_NS, 'circle');
  head.setAttribute('class', 'shooting-star-head');
  head.setAttribute('r', '2');
  head.setAttribute('cx', String(x));
  head.setAttribute('cy', String(y));
  head.style.opacity = '0';

  svg.append(defs, arcProbe, trail, head);
  scene.appendChild(svg);

  animateMeteor(svg, arcProbe, trail, trailGradient, head, pathLength, trailLength, durationMs);
}

function prefersReducedMotion(): boolean {
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches;
}

/** Builds stars and starts meteor scheduling; returns cleanup for unmount. */
export function initSkyAnimation(
  starContainer: SVGGElement,
  scene: HTMLElement,
): () => void {
  buildStarField(starContainer);

  const timeouts: number[] = [];
  let cancelled = false;

  const scheduleMeteorLoop = () => {
    if (cancelled) {
      return;
    }

    const delay = randRange(
      Math.random,
      METEOR_MIN_INTERVAL_MS,
      METEOR_MAX_INTERVAL_MS,
    );

    const timeoutId = window.setTimeout(() => {
      if (!cancelled) {
        spawnMeteor(scene);
        scheduleMeteorLoop();
      }
    }, delay);

    timeouts.push(timeoutId);
  };

  if (!prefersReducedMotion()) {
    const initialTimeoutId = window.setTimeout(() => {
      if (!cancelled) {
        spawnMeteor(scene);
        scheduleMeteorLoop();
      }
    }, 1200);
    timeouts.push(initialTimeoutId);
  }

  return () => {
    cancelled = true;
    timeouts.forEach((timeoutId) => {
      window.clearTimeout(timeoutId);
    });
    scene.querySelectorAll('.shooting-star').forEach((element) => {
      element.remove();
    });
  };
}
