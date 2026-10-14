    // ===== tudo que mexe no header e nas animações mora aqui =====
    const topo = document.getElementById('topo');
    if (!topo) {
        console.warn('CredMais: elemento #topo não encontrado.');
    }
    else {
        const links = [...topo.querySelectorAll('a')];
        const marcador = topo.querySelector('.marcador');
        const secoes = [...document.querySelectorAll('[data-secao]')];
        const semMovimento =
            window.matchMedia( '(prefers-reduced-motion: reduce)').matches;
        let atual = null;
        let rolandoPorClique = false;
        let quadro;
        // ---------- barrinha azul ----------
        const ESCALA = 1.06;
        function posicionarMarcador(animar = true) {
            const link = topo.querySelector('a.ativo');
            if (!link) {
                return;
            }
            marcador.style.transition =
                animar ? '' : 'none';
            marcador.style.width =
                link.offsetWidth * ESCALA + 'px';
            marcador.style.transform =
                `translateX(${
                    link.offsetLeft -
                    link.offsetWidth *
                    (ESCALA - 1) / 2
                }px)`;
            if (!animar) {
                marcador.offsetWidth;
                marcador.style.transition = '';
            }
        }
        function ativar(id, animar = true) {
            if (id === atual) {
                return;
            }
            atual = id;
            links.forEach(link => {
                const ehEsse =
                    link.getAttribute('href') === '#' + id;
                link.classList.toggle(
                    'ativo',
                    ehEsse
                );
                if (ehEsse) {
                    link.setAttribute(
                        'aria-current',
                        'true'
                    );
                } else {
                    link.removeAttribute(
                       'aria-current'
                    );
                }
            });
            posicionarMarcador(animar);
        }
        // ---------- qual seção está na tela? ----------
        function descobrirSecao() {
            const linha = window.innerHeight * 0.4;
            let id =
                secoes.length
                    ? secoes[0].dataset.secao
                    : 'inicio';
            secoes.forEach(s => {
                if (
                    s.getBoundingClientRect().top <=
                    linha
                ) {
                    id = s.dataset.secao;
                }
            });
            const fimDaPagina =
                window.innerHeight +
                window.scrollY >=
                document.documentElement.scrollHeight - 4;
            return fimDaPagina
                ? 'contato'
                : id;
        }
        // ---------- rolagem suave ----------
        function rolarAte(alvo) {
            if (!alvo) {
                return;
            }
            const topoDoAlvo =
                alvo.id === 'inicio'
                    ? 0
                    : alvo.getBoundingClientRect().top +
                      window.scrollY -
                      topo.offsetHeight;
            const maximo =
                document.documentElement.scrollHeight -
                window.innerHeight;
            const fim =
                Math.max(
                    0,
                    Math.min(
                        topoDoAlvo,
                        maximo
                    )
                );
            const inicio =
                window.scrollY;
            const distancia =
                fim - inicio;
            if (
                semMovimento ||
                Math.abs(distancia) < 2
            ) {
                window.scrollTo(
                    0,
                    fim
                );

                return;
            }


            const duracao =
                Math.min(
                    1200,
                    Math.max(
                        700,
                        Math.abs(distancia) * 0.8
                    )
                );


            const comeco =
                performance.now();


            rolandoPorClique = true;


            function passo(agora) {

                const t =
                    Math.min(
                        (agora - comeco) /
                        duracao,
                        1
                    );
                const suave =
                    t < 0.5
                        ? 4 * t * t * t
                        : 1 -
                          Math.pow(
                              -2 * t + 2,
                              3
                          ) / 2;
                window.scrollTo(
                    0,
                    inicio +
                    distancia * suave
                );
                if (t < 1) {
                    quadro =
                        requestAnimationFrame(
                            passo
                        );
                } else {
                    setTimeout(
                        () => {
                            rolandoPorClique = false;
                        },
                        120
                    );
                }
            }
            quadro =
                requestAnimationFrame(
                    passo
                );
        }
        // ---------- interromper rolagem manual ----------
        ['wheel', 'touchmove'].forEach(
            evento => {
                window.addEventListener(
                    evento,
                    () => {
                        cancelAnimationFrame(
                            quadro
                        );
                        rolandoPorClique = false;
                    },
                    {
                        passive: true
                    }
                );
            }
        );
        // ---------- clique no menu ----------
        links.forEach(link => {
            link.addEventListener(
                'click',
                e => {
                    e.preventDefault();
                    const id =
                        link
                            .getAttribute('href')
                            .slice(1);
                    ativar(id);
                    rolarAte(
                        document.getElementById(id)
                    );
                    history.replaceState(
                        null,
                        '',
                        '#' + id
                    );
                }
            );
        });
        // ---------- scroll ----------
        let esperando = false;
        function aoRolar() {
            if (esperando) {
                return;
            }
            esperando = true;

            requestAnimationFrame(
                () => {
                    esperando = false;
                    topo.classList.toggle(
                        'colado',
                        window.scrollY > 40
                    );
                    if (!rolandoPorClique) {
                        ativar(
                            descobrirSecao()
                        );
                    }
                }
            );
        }
        window.addEventListener(
            'scroll',
            aoRolar,
            {
                passive: true
            }
        );
        // ---------- animações de entrada ----------
        document
            .querySelectorAll(
                '.card, .motivo, .passo, ' +
                '.objetivo > *, ' +
                '.secao > h2, ' +
                '.secao > .sobretitulo, ' +
                '.secao > .subtitulo'
            )
            .forEach(
                el => {
                    el.classList.add(
                        'revelar'
                    );
                }
            );
        // ---------- IntersectionObserver ----------
        const observador =
            'IntersectionObserver' in window
                ? new IntersectionObserver(
                    entradas => {
                        entradas.forEach(
                            entrada => {
                                if (
                                    entrada.isIntersecting
                                ) {
                                    entrada.target.classList.add(
                                        'visivel'
                                    );
                                    observador.unobserve(
                                        entrada.target
                                    );
                                }
                            }
                        );
                    },
                    {
                        threshold: 0.15
                    }
                )
                : null;
        if (observador) {
            document
                .querySelectorAll('.revelar')
                .forEach(
                    el => {
                        observador.observe(el);
                    }
                );
        }
        // ---------- arranque ----------
        topo.classList.toggle(
            'colado',
            window.scrollY > 40
        );
        ativar(
            descobrirSecao(),
            false
        );
        if (document.fonts) {
            document.fonts.ready.then(
                () => {
                    posicionarMarcador(
                        false
                    );
                }
            );
        }
        window.addEventListener(
            'resize',
            () => {
                posicionarMarcador(
                    false
                );
            }
        );
    }